from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.chains import RetrievalQA

from src.utils.logger import get_logger
from src.services.database_manager.connection import get_db_connection_string

# --- Setup ---

# Load environment variables from both configuration files
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Initialize logger for this module
logger = get_logger(__name__)


class VectorSearchService:
    """
    A service for searching and querying document and learning embeddings
    from a unified vector store.
    """

    def __init__(self):
        """
        Initializes the search service, setting up connections and retrieval chains.
        """
        session_id = "vector-search-init"
        log_extra = {"session_id": session_id}
        logger.info("Initializing VectorSearchService...", extra=log_extra)

        # 1. Construct PostgreSQL connection string
        connection = get_db_connection_string()

        # 2. Initialize embeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        # 3. Connect to the existing PGVector store
        self.vector_store = PGVector.from_existing_index(
            embedding=embeddings,
            collection_name="developer_docs",
            connection=connection,
            use_jsonb=True,
        )

        # 4. Initialize LLM and Retrievers
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        doc_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5, "filter": {"type": "documentation"}}
        )
        learning_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3, "filter": {"type": "learning"}}
        )

        # 5. Initialize QA Chains
        self.doc_qa_chain = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=doc_retriever
        )

        learning_prompt_template = """
        Based on the context below, find the most relevant learning resource for the user's query.
        Return only the title and the URL in the format: "Found learning resource: '[TITLE]'. View it here: [URL]"
        If no relevant resource is found, state that clearly.

        Context:
        {context}

        Query: {question}
        """
        learning_prompt = PromptTemplate(
            template=learning_prompt_template, input_variables=["context", "question"]
        )
        self.learning_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=learning_retriever,
            chain_type_kwargs={"prompt": learning_prompt},
        )

        logger.info("VectorSearchService initialized successfully.", extra=log_extra)

    def search_documentation(self, query: str, session_id: str = "anonymous") -> str:
        """
        Searches documentation for a given query.
        """
        log_extra = {"session_id": session_id}
        logger.info(f"Received documentation search query: '{query}'", extra=log_extra)
        try:
            result = self.doc_qa_chain.invoke({"query": query})
            return result.get("result", "Could not find an answer in the documentation.")
        except Exception as e:
            logger.error(f"An error occurred during documentation search: {e}", extra=log_extra, exc_info=True)
            return "Error: An unexpected error occurred while searching documentation."

    def search_learnings(self, query: str, session_id: str = "anonymous") -> str:
        """
        Searches learning resources for a given query.
        """
        log_extra = {"session_id": session_id}
        logger.info(f"Received learning search query: '{query}'", extra=log_extra)
        try:
            result = self.learning_qa_chain.invoke({"query": query})
            return result.get("result", "No specific learning resources found for that query.")
        except Exception as e:
            logger.error(f"An error occurred during learning search: {e}", extra=log_extra, exc_info=True)
            return "Error: An unexpected error occurred while searching learning resources."


if __name__ == "__main__":
    try:
        search_service = VectorSearchService()
        
        # --- Test Documentation Search ---
        doc_query = "What can you tell me about the ChimeraCI project?"
        print(f"--- Running Documentation Search ---")
        print(f"Query: {doc_query}")
        doc_answer = search_service.search_documentation(doc_query, session_id="test-doc-search")
        print("\\n--- Generated Answer ---")
        print(doc_answer)
        print("\\n" + "-"*20 + "\\n")

        # --- Test Learning Search ---
        learning_query = "How to optimize lazy loading?"
        print(f"--- Running Learning Search ---")
        print(f"Query: {learning_query}")
        learning_answer = search_service.search_learnings(learning_query, session_id="test-learning-search")
        print("\\n--- Generated Answer ---")
        print(learning_answer)
        print("\\n--- Test Complete ---")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}") 