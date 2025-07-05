import os
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from src.utils.logger import get_logger

# --- Setup ---

# Load environment variables from both configuration files
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Initialize logger for this module
logger = get_logger(__name__)
SESSION_ID = "learning-embed"
log_extra = {"session_id": SESSION_ID}

# --- Database Configuration ---

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")  # Password is now optional

if not all([PG_HOST, PG_PORT, PG_DB, PG_USER]):
    raise ValueError("PG_HOST, PG_PORT, PG_DB, and PG_USER environment variables must be set.")

user_info = PG_USER if PG_USER else ""
if PG_PASSWORD:
    user_info += f":{PG_PASSWORD}"

connection = f"postgresql+psycopg://{user_info}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# --- General Configuration ---

LEARNING_FILE_PATH = Path("data/learning.json")
EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "developer_docs"


def embed_learning_resources():
    """
    Reads learning resources from a JSON file, creates Document objects,
    and stores their embeddings in the vector store.
    """
    logger.info("Starting learning resources embedding process.", extra=log_extra)

    # 1. Read and prepare documents from JSON
    if not LEARNING_FILE_PATH.exists():
        logger.error(f"Learning resources file not found at {LEARNING_FILE_PATH}", extra=log_extra)
        return

    with open(LEARNING_FILE_PATH, "r", encoding="utf-8") as f:
        learning_items = json.load(f)

    documents_to_add = []
    for item in learning_items:
        content = f"{item.get('title', '')}\\n\\n{item.get('summary', '')}"
        metadata = {
            "source": "learning",
            "title": item.get("title"),
            "category": item.get("category"),
            "url": item.get("url"),
            "tags": ", ".join(item.get("tags", [])), # Store tags as a single string
        }
        doc = Document(page_content=content, metadata=metadata)
        documents_to_add.append(doc)

    if not documents_to_add:
        logger.warning("No learning items found to embed.", extra=log_extra)
        return

    # 2. Initialize embedding model
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # 3. Add documents to the existing collection in one step
    PGVector.from_documents(
        embedding=embeddings,
        documents=documents_to_add,
        collection_name=COLLECTION_NAME,
        connection=connection,
        use_jsonb=True,
    )
    
    logger.info(
        f"Successfully embedded {len(documents_to_add)} learning items into the vector store.",
        extra=log_extra,
    )
    print(f"\\nDone embedding {len(documents_to_add)} learning items into the '{COLLECTION_NAME}' collection.")


if __name__ == "__main__":
    # Example of running with a few sample records for testing
    # To run with all items, simply call embed_learning_resources()
    try:
        embed_learning_resources()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", extra=log_extra, exc_info=True)
        print(f"An error occurred. Check the logs at {os.getenv('LOG_DIRECTORY')}.") 