import os
import json
from typing import TypedDict, Annotated, Optional, cast

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text, Engine

from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel

from src.utils.logger import get_logger
from src.utils.database import get_engine

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")
logger = get_logger(__name__)

# --- State Definition for Type Hinting ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]
    user_id: str
    is_sql_query: bool
    selected_ticket_id: Optional[str]
    selected_project_id: Optional[str]

# --- Pydantic Schema for Structured Output ---
class NL2SQLResult(BaseModel):
    query: str = Field(description="The executable SQL query generated from the user's question.")
    confidence: float = Field(description="A confidence score between 0.0 and 1.0 for the generated query.")
    explanation: str = Field(description="A brief explanation of what the SQL query is doing.")

# --- NL2SQL Service Class ---
class NL2SQLService:
    """A service that converts natural language to SQL, executes it, and returns the result."""

    def __init__(self, llm: BaseLanguageModel, db_engine: Engine):
        self.db_engine = db_engine
        self.output_parser = llm.with_structured_output(NL2SQLResult)
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
        """Creates the system prompt with schema, guidelines, and few-shot examples."""
        return """
You are an expert SQL generator for a developer assistance agent. Your task is to convert a user's natural language question into a PostgreSQL query.

### Database Schema
- users (id UUID, name TEXT, email TEXT, role TEXT)
- projects (id UUID, name TEXT, description TEXT)
- jira_tickets (id UUID, title TEXT, description TEXT, status TEXT, assigned_to UUID, project_id UUID)
- pull_requests (id UUID, title TEXT, summary TEXT, ticket_id UUID, author_id UUID, project_id UUID)
- git_diffs (id UUID, diff_text TEXT, pr_id UUID)

### Table Joins
- `jira_tickets.project_id` can be joined with `projects.id`.
- `jira_tickets.assigned_to` can be joined with `users.id`.
- `pull_requests.ticket_id` can be joined with `jira_tickets.id`.

### Keyword & Synonym Mapping
When searching for keywords in `jira_tickets`, expand the search to include common synonyms:
- For "bug fixes" or "bug", search for terms like '%bug%' or '%fix%'.
- For "TD" or "Tech Debt", search for '%technical debt%'.
- For "feature", search for '%feature%'.

### Status Value Mapping
When a user asks about ticket status, map conversational terms to database values. The `status` column can be 'Open', 'In Progress', or 'Done'.
- For "completed" or "finished" tickets, use `LOWER(status) = 'done'`.
- For tickets the user is "doing", "working on", or are "in progress", use `LOWER(status) = 'in progress'`.
- For "open" tickets or tickets "yet to be started", use `LOWER(status) = 'open'`.

### Query Guidelines
- Support queries on Jira tickets by status, keyword (in title/description), or counts.
- **IMPORTANT**: When filtering by `status` on `jira_tickets`, use the `LOWER()` function for case-insensitive comparison (e.g., `LOWER(status) = 'open'`).
- To query pull requests, a `ticket_id` must be available.
- Generate only a single, executable SQL statement.

### RBAC Enforcement
**CRITICAL:** You MUST enforce Role-Based Access Control (RBAC) in every query.

### Few-Shot Examples
Human: Show all open Jira tickets
Assistant: SELECT jt.id, jt.title, jt.status, p.name as project_name FROM jira_tickets jt JOIN projects p ON jt.project_id = p.id WHERE LOWER(jt.status) = 'open' AND jt.assigned_to = :user_id

Human: Find my tickets related to bug fixes
Assistant: SELECT jt.id, jt.title, p.name AS project_name FROM jira_tickets jt JOIN projects p ON jt.project_id = p.id WHERE (LOWER(jt.title) LIKE '%bug%' OR LOWER(jt.title) LIKE '%fix%' OR LOWER(jt.description) LIKE '%bug%' OR LOWER(jt.description) LIKE '%fix%') AND jt.assigned_to = :user_id

Human: How many tickets have I completed?
Assistant: SELECT COUNT(*) FROM jira_tickets WHERE LOWER(status) = 'done' AND assigned_to = :user_id

Human: Count my Jira tickets by status
Assistant: SELECT status, COUNT(*) FROM jira_tickets WHERE assigned_to = :user_id GROUP BY status

Human: List PRs for ticket '123e4567-e89b-12d3-a456-426614174000'
Assistant: SELECT pr.id, pr.status, pr.created_at FROM pull_requests pr JOIN jira_tickets jt ON pr.ticket_id = jt.id WHERE jt.id = '123e4567-e89b-12d3-a456-426614174000' AND jt.assigned_to = :user_id
"""

    def __call__(self, state: AgentState) -> dict:
        """
        The main entry point for the NL2SQL node.
        Converts natural language to SQL, executes it, and returns the result.
        """
        user_query = state["messages"][-1].content
        user_id = state["user_id"]
        log_extra = {"user_id": user_id, "session_id": "nl2sql_node"}
        logger.info(f"Received NL2SQL query: '{user_query}'", extra=log_extra)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{user_query}")
        ])
        
        chain = prompt | self.output_parser
        nl2sql_result = cast(NL2SQLResult, chain.invoke({"user_query": user_query}))

        logger.info(f"Generated SQL: {nl2sql_result.query}", extra=log_extra)

        with self.db_engine.connect() as connection:
            try:
                # Execute the query with the user_id as a parameter to prevent SQL injection
                results = connection.execute(
                    text(nl2sql_result.query),
                    {"user_id": user_id}
                ).mappings().all()
                
                query_results = [dict(row) for row in results]
                logger.info(f"SQL query returned {len(query_results)} results.", extra=log_extra)
                
                # Create a dictionary of results
                nl2sql_response = {
                    "query": nl2sql_result.query,
                    "explanation": nl2sql_result.explanation,
                    "confidence": nl2sql_result.confidence,
                    "results": query_results,
                }
                return {"nl2sql_results": nl2sql_response}

            except Exception as e:
                logger.error(f"Failed to execute SQL query: {e}", extra=log_extra, exc_info=True)
                error_response = {
                    "error": f"Error: Failed to execute SQL query. Please check your query or the database. Details: {str(e)}",
                }
                return {"nl2sql_results": error_response}

if __name__ == "__main__":
    import sys
    from langchain_core.messages import HumanMessage

    # 1. Setup DB Engine
    engine = get_engine()

    # 2. Get a test user_id and ticket_id
    test_user_id = "72bf36a1-5491-44dc-975d-2fd28dc379a7"
    test_ticket_id = None
    try:
        with engine.connect() as connection:
            user_result = connection.execute(text("SELECT id FROM users LIMIT 1")).first()
            if user_result:
                test_user_id = str(user_result[0])
                ticket_result = connection.execute(
                    text("SELECT id FROM jira_tickets WHERE assigned_to = :user_id LIMIT 1"),
                    {"user_id": test_user_id}
                ).first()
                if ticket_result:
                    test_ticket_id = str(ticket_result[0])
    except Exception as e:
        print(f"Database connection failed. Please ensure the database is running and configured. Error: {e}")
        sys.exit(1)

    if not test_user_id:
        print("Could not find a user in the database. Please populate the database and run the script again.")
        sys.exit(0)

    # 3. Setup LLM and Service
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    nl2sql_service = NL2SQLService(llm=llm, db_engine=engine)

    # 4. Define test queries
    test_queries = [
        "Show all my open Jira tickets",
        "How many tickets do I have in progress?",
        "count my tickets",
    ]
    if test_ticket_id:
        test_queries.append(f"List the pull requests for ticket {test_ticket_id}")
    else:
        print("Warning: Could not find a ticket for the test user. Skipping PR query test.")

    # 5. Run tests
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        
        mock_state = {
            "messages": [HumanMessage(content=query)],
            "user_id": test_user_id,
            "is_sql_query": True,
            "selected_ticket_id": None,
            "selected_project_id": None
        }

        result = nl2sql_service(cast(AgentState, mock_state))
        print(json.dumps(result, indent=2, default=str))
        print("-" * (len(query) + 22)) 