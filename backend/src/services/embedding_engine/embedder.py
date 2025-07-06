import psycopg  
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.text_splitter import MarkdownTextSplitter

from src.utils.logger import get_logger
from src.services.database_manager.connection import get_db_connection_string

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

logger = get_logger(__name__)
SESSION_ID = "embedding_script"
log_extra = {"session_id": SESSION_ID}


class EmbeddingEngine:
    """
    A class to handle fetching, chunking, and embedding of documents and learnings.
    """

    def __init__(self):
        """Initializes the EmbeddingEngine."""
        logger.info("Initializing EmbeddingEngine...", extra=log_extra)
        self._load_config()
        self.connection_string = get_db_connection_string()
        self.direct_connection_str = get_db_connection_string(driver="psycopg2")
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
        self.text_splitter = MarkdownTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )

    def _load_config(self):
        """Loads configuration from environment variables."""
        self.collection_name = "developer_docs"
        self.embedding_model = "text-embedding-3-large"
        self.chunk_size = 500
        self.chunk_overlap = 200

    def _get_db_connection(self):
        """Establishes a direct psycopg connection to the database."""
        try:
            conn = psycopg.connect(self.direct_connection_str)
            logger.info("Database connection established successfully.", extra=log_extra)
            return conn
        except psycopg.OperationalError as e:
            logger.error(f"Database connection failed: {e}", extra=log_extra)
            raise

    def _fetch_documents(self, conn, limit=None):
        """Fetches documentation records from the database."""
        logger.info("Fetching documents from the database.", extra=log_extra)
        with conn.cursor() as cur:
            query = """
                SELECT d.title, d.content, d.type, p.name as project_name
                FROM documents d
                JOIN projects p ON d.project_id = p.id
            """
            if limit:
                query += f" LIMIT {limit}"
            cur.execute(query)
            records = cur.fetchall()
            logger.info(f"Fetched {len(records)} document records.", extra=log_extra)
            return records

    def _fetch_learnings(self, conn, limit=None):
        """Fetches learning records from the database."""
        logger.info("Fetching learnings from the database.", extra=log_extra)
        with conn.cursor() as cur:
            query = "SELECT title, summary, tags, urls FROM learnings"
            if limit:
                query += f" LIMIT {limit}"
            cur.execute(query)
            records = cur.fetchall()
            logger.info(f"Fetched {len(records)} learning records.", extra=log_extra)
            return records

    def _prepare_and_embed_data(self, documents, learnings):
        """Prepares, chunks, and embeds data into the vector store."""
        all_docs = []
        for record in documents:
            doc_title, content, doc_type, project_name = record
            metadata = {
                "doc_title": doc_title, "document_type": doc_type,
                "project_name": project_name, "type": "documentation",
            }
            all_docs.append(Document(page_content=content, metadata=metadata))

        for record in learnings:
            title, summary, tags, urls = record
            content = f"Title: {title}\\nSummary: {summary}"
            metadata = {
                "learning_title": title, "tags": tags or [],
                "urls": urls or [], "type": "learning",
            }
            all_docs.append(Document(page_content=content, metadata=metadata))

        if not all_docs:
            logger.warning("No documents or learnings to process.", extra=log_extra)
            return 0

        logger.info(f"Prepared a total of {len(all_docs)} documents for splitting.", extra=log_extra)
        split_chunks = self.text_splitter.split_documents(all_docs)
        logger.info(f"Split documents into {len(split_chunks)} chunks.", extra=log_extra)

        if not split_chunks:
            logger.warning("No chunks were created from the documents.", extra=log_extra)
            return 0

        logger.info(f"Embedding {len(split_chunks)} chunks into collection '{self.collection_name}'...", extra=log_extra)
        PGVector.from_documents(
            embedding=self.embeddings,
            documents=split_chunks,
            collection_name=self.collection_name,
            connection=self.connection_string,
            use_jsonb=True,
            pre_delete_collection=True
        )
        logger.info("Successfully embedded all chunks.", extra=log_extra)
        return len(split_chunks)

    def run_embedding_pipeline(self, doc_limit=None, learning_limit=None):
        """Full pipeline to fetch, process, and embed data."""
        conn = None
        try:
            conn = self._get_db_connection()
            documents = self._fetch_documents(conn, limit=doc_limit)
            learnings = self._fetch_learnings(conn, limit=learning_limit)
            
            num_vectors = self._prepare_and_embed_data(documents, learnings)
            
            print(f"\\n--- Embedding Complete ---")
            print(f"Successfully inserted {num_vectors} vectors into the '{self.collection_name}' collection.")
            print("--------------------------\\n")

        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed.", extra=log_extra)


if __name__ == "__main__":
    logger.info("Running embedding script in test mode.", extra=log_extra)
    try:
        engine = EmbeddingEngine()
        engine.run_embedding_pipeline()
    except Exception as e:
        logger.error(f"An unexpected error occurred during the test run: {e}", extra=log_extra, exc_info=True)
        print(f"An error occurred. Check logs for details.")
