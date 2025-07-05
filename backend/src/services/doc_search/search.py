import os
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.chains import RetrievalQA

from src.utils.logger import get_logger

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

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
        pg_host = os.getenv("PG_HOST")
        pg_port = os.getenv("PG_PORT")
        pg_db = os.getenv("PG_DB")
        pg_user = os.getenv("PG_USER")
        pg_password = os.getenv("PG_PASSWORD")

        if not all([pg_host, pg_port, pg_db, pg_user]):
            raise ValueError("Required PostgreSQL environment variables are not set.")

        user_info = pg_user or ""
        if pg_password:
            user_info += f":{pg_password}"

        connection = (
            f"postgresql+psycopg://{user_info}@{pg_host}:{pg_port}/{pg_db}"
        )

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