import os
import uuid
import json
from pathlib import Path
from typing import TypedDict, Annotated, Literal, Hashable, cast, Optional

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.utils.logger import get_logger
from src.services.agent.tools import (
    pr_diff_tool,
    pr_summary_tool,
    doc_search_tool,
    learning_search_tool,
)
from src.services.agent.nl2sql import NL2SQLService

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")
logger = get_logger(__name__)

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]
    user_id: str
    is_sql_query: bool
    selected_ticket_id: Optional[str]
    selected_project_id: Optional[str]
    nl2sql_results: Optional[dict]

# --- Agent Class ---
class ChatAgent:
    def __init__(self):
        logger.info("Initializing ChatAgent...")
        self.tools = [
            pr_diff_tool,
            pr_summary_tool,
            doc_search_tool,
            learning_search_tool,
        ]
        self.tool_map = {tool.name: tool for tool in self.tools}

        # Model for planning (deciding which tool to use)
        self.planner_model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
        self.planner_model = self.planner_model.bind_tools(self.tools)

        # Model for generating the final response
        self.responder_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, streaming=True)
        
        # Model for SQL generation
        self.sql_generation_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # NL2SQL Service
        db_engine = self._get_db_engine()
        self.nl2sql_service = NL2SQLService(llm=self.sql_generation_llm, db_engine=db_engine)

        self.graph = self.build_graph()
        logger.info("ChatAgent graph built successfully.")

    def _get_db_engine(self):
        pg_host = os.getenv("PG_HOST")
        pg_port = os.getenv("PG_PORT")
        pg_db = os.getenv("PG_DB")
        pg_user = os.getenv("PG_USER")
        pg_password = os.getenv("PG_PASSWORD")
        user_info = pg_user or ""
        if pg_password:
            user_info += f":{pg_password}"
        db_url = f"postgresql+psycopg://{user_info}@{pg_host}:{pg_port}/{pg_db}"
        return create_engine(db_url)

    def build_graph(self):
        graph = StateGraph(AgentState)
        
        graph.add_node("router", self.route_query)
        graph.add_node("nl2sql_node", self.nl2sql_service)
        graph.add_node("planner", self.call_planner)
        graph.add_node("tool_executor", self.call_tool_executor)
        graph.add_node("generate_response", self.generate_response_node)

        graph.set_entry_point("router")

        graph.add_conditional_edges(
            "router",
            lambda state: "nl2sql_node" if state.get("is_sql_query") else "planner",
            {
                "nl2sql_node": "nl2sql_node",
                "planner": "planner",
            }
        )
        
        tool_executor_map: dict[Hashable, str] = {tool.name: "tool_executor" for tool in self.tools}
        tool_executor_map["generate_response"] = "generate_response"
        graph.add_conditional_edges(
            "planner", self.route_tool_action, tool_executor_map
        )
        
        graph.add_edge("tool_executor", "planner")
        graph.add_edge("nl2sql_node", "generate_response")
        graph.add_edge("generate_response", END)

        checkpointer = InMemorySaver()
        runnable = graph.compile(checkpointer=checkpointer)
        self.save_graph_visualization(runnable)
        return runnable

    def save_graph_visualization(self, runnable):
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        try:
            png_data = runnable.get_graph(xray=True).draw_mermaid_png()
            with open(artifacts_dir / "chat_graph.png", "wb") as f:
                f.write(png_data)
            logger.info("Saved agent graph visualization to artifacts/chat_graph.png")
        except Exception as e:
            logger.warning(f"Failed to draw graph. Is pygraphviz installed? Error: {e}")

    def route_query(self, state: AgentState):
        last_message = state["messages"][-1].content
        classifier_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert classifier. Determine if a user's query should be answered by querying a database with SQL or by using other tools. Database queries involve asking for lists, counts, or details about 'tickets', 'bugs', 'features', or 'tasks'. Respond with 'database' or 'general'."),
            ("human", "{user_query}")
        ])
        chain = prompt | classifier_model | StrOutputParser()
        result = chain.invoke({"user_query": last_message})
        is_sql = "database" in result.lower()
        logger.info(f"Query classified as {'SQL' if is_sql else 'General'}")
        return {"messages": state["messages"], "is_sql_query": is_sql}
        
    def call_planner(self, state: AgentState):
        response = self.planner_model.invoke(state["messages"])
        return {"messages": [response]}

    def generate_response_node(self, state: AgentState):
        system_template = """You are a helpful assistant. Synthesize a final response for the user based on the conversation history. Be concise and answer the user's question directly.
{context}"""

        nl2sql_results = state.get("nl2sql_results")
        context_string = ""

        if nl2sql_results:
            # Format the SQL results as a string to be injected into the prompt.
            context_string = f"\\nHere is some context from a database query that was run to help answer the user's question. Use this to formulate your response:\\n\\n{json.dumps(nl2sql_results, indent=2, default=str)}"
        elif any(isinstance(m, ToolMessage) for m in state["messages"]):
            # For the regular tool path, the tool output is already in the message history.
            context_string = "\\nIf the last message is a tool output, summarize it for the user."

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        chain = prompt | self.responder_model
        response = chain.invoke({
            "messages": state["messages"],
            "context": context_string
        })
        return {"messages": [response]}

    def call_tool_executor(self, state: AgentState):
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return {}

        tool_call = last_message.tool_calls[0]
        tool_args = tool_call["args"]
        if state.get("user_id"):
            tool_args["user_id"] = state["user_id"]
        
        observation = self.tool_map[tool_call["name"]].invoke(tool_args)
        return {"messages": [ToolMessage(content=str(observation), tool_call_id=tool_call["id"])]}

    def route_tool_action(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "generate_response"
        return last_message.tool_calls[0]["name"]

    def run(self, user_query: str, user_id: str, session_id: str | None = None):
        session_id = session_id or str(uuid.uuid4())
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "user_id": user_id,
            "is_sql_query": False,
            "selected_ticket_id": None,
            "selected_project_id": None,
        }
        
        final_state = self.graph.invoke(cast(AgentState, initial_state), config=config)
        return final_state['messages'][-1].content

if __name__ == "__main__":
    agent = ChatAgent()
    test_user_id = "fcb7fd5e-4942-4385-96cc-6765a3c1f553" # Vito Corleone
    
    test_prompts = [
        "What are my open Jira tickets?",
        "Find my tickets related to 'bug fixes'.",
        "How do I set up and run the local development environment?",
        "Summarize the PR for ticket_id 'your-ticket-id-here'", # Replace with a real ticket ID from a run
    ]
    
    thread_id = str(uuid.uuid4())
    print(f"--- Using Session/Thread ID: {thread_id} for user: {test_user_id} ---")

    for i, prompt in enumerate(test_prompts):
        print(f"\\n--- Test Prompt {i+1} ---")
        print(f"Input: {prompt}")
        # Manual injection for test case
        if "your-ticket-id-here" in prompt:
            # In a real scenario, this would be retrieved from a previous turn
            first_ticket_id = "22e5d89c-96eb-4bed-b807-6e29c897e5b0"
            prompt = prompt.replace("your-ticket-id-here", first_ticket_id)

        final_response = agent.run(prompt, user_id=test_user_id, session_id=thread_id)
        print(f"Output: {final_response}")
        print("-" * (20 + len(str(i+1)))) 