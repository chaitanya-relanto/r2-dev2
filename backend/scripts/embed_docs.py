import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.text_splitter import MarkdownTextSplitter

from src.utils.logger import get_logger

# --- Setup ---

# Load environment variables from both configuration files
# Assumes the script is run from the project root
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Initialize logger for this module
logger = get_logger(__name__)
SESSION_ID = "doc-embed"
log_extra = {"session_id": SESSION_ID}

# --- Database Configuration ---

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")  # Password is now optional

# Check for required variables; PG_PASSWORD is not required
if not all([PG_HOST, PG_PORT, PG_DB, PG_USER]):
    raise ValueError("PG_HOST, PG_PORT, PG_DB, and PG_USER environment variables must be set.")

# Conditionally construct the user info part of the connection string
user_info = PG_USER if PG_USER else ""
if PG_PASSWORD:
    user_info += f":{PG_PASSWORD}"

# Construct the final connection string
connection = f"postgresql+psycopg://{user_info}@{PG_HOST}:{PG_PORT}/{PG_DB}"

logger.info(
    f"Constructed PostgreSQL connection string for host: {PG_HOST}, port: {PG_PORT}, db: {PG_DB}",
    extra=log_extra,
)

# --- General Configuration ---

# Path to the documentation files
DOCS_PATH = Path("data/docs")

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-large"

# Vector store configuration
COLLECTION_NAME = "developer_docs"

# Text splitter configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200


def embed_documents():
    """
    Reads markdown files, splits them into chunks, generates embeddings,
    and stores them in a PostgreSQL vector store.
    """
    logger.info("Starting document embedding process.", extra=log_extra)

    # 1. Read and prepare documents
    all_docs = []
    # Recursively find all markdown files
    doc_files = list(DOCS_PATH.rglob("*.md"))
    
    if not doc_files:
        logger.warning(f"No markdown files found in {DOCS_PATH}. Exiting.", extra=log_extra)
        return

    for doc_path in doc_files:
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Use relative path for file_name and add source
            relative_path = str(doc_path.relative_to(DOCS_PATH))
            doc = Document(
                page_content=content,
                metadata={
                    "file_name": relative_path,
                    "source": "documentation",
                },
            )
            all_docs.append(doc)
        except Exception as e:
            logger.error(f"Failed to read or process {doc_path.name}: {e}", extra=log_extra)

    # 2. Split documents into chunks
    text_splitter = MarkdownTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    split_chunks = text_splitter.split_documents(all_docs)

    logger.info(f"Total documents split into {len(split_chunks)} chunks.", extra=log_extra)
    
    # Log chunk count per file using a more robust method
    file_paths_in_chunks = sorted(list(set(chunk.metadata["file_name"] for chunk in split_chunks)))
    for file_path in file_paths_in_chunks:
        chunk_count = sum(1 for chunk in split_chunks if chunk.metadata["file_name"] == file_path)
        logger.info(f"File '{file_path}' was split into {chunk_count} chunks.", extra=log_extra)

    # 3. Initialize embedding model
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    # 4. Create vector store and add documents in one step
    if split_chunks:
        PGVector.from_documents(
            embedding=embeddings,
            documents=split_chunks,
            collection_name=COLLECTION_NAME,
            connection=connection,
            use_jsonb=True,
            pre_delete_collection=True
        )
        logger.info(
            f"Successfully embedded and stored {len(doc_files)} files in the vector store.",
            extra=log_extra,
        )
        print(f"\\nDone embedding {len(doc_files)} files into the '{COLLECTION_NAME}' collection.")
    else:
        logger.warning("No document chunks to embed.", extra=log_extra)
        print("\\nNo new documents were embedded.")


if __name__ == "__main__":
    try:
        embed_documents()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", extra=log_extra, exc_info=True)
        print(f"An error occurred. Check the logs at {os.getenv('LOG_DIRECTORY')}.") 