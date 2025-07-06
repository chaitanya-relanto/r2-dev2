import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import SecretStr

# Add project root to path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logger import get_logger
from src.services.database_manager import operations as db_ops

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

logger = get_logger(__name__)


# --- LLM Elaborator ---
class DocElaborator:
    """A service to elaborate on documentation content using an LLM."""
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in the environment variables.")
            raise ValueError("OPENAI_API_KEY must be set to elaborate documents.")
        
        self.llm = ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini", temperature=0.4)
        logger.info("DocElaborator initialized.")

    def elaborate_markdown(self, title: str, content: str) -> str:
        """Uses an LLM to elaborate on markdown content."""
        logger.info(f"Elaborating content for document: '{title}'")
        system_prompt = (
            "You are an expert technical documentation writer. Given the title and existing content "
            "of a project's documentation, elaborate and rewrite it into a more complete, clear, and "
            "detailed Markdown guide suitable for developers. Preserve the original intent but expand "
            "on it with examples, better structure, and clear explanations. Ensure the final output "
            "is pure, well-formatted markdown. Ensure not to use any code blocks in the output."
        )

        human_prompt = f"Please elaborate on the following documentation:\n\nTitle: {title}\n\nContent:\n{content}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            elaborated_content = str(response.content)
            logger.info(f"Successfully elaborated content for '{title}'.")
            return elaborated_content
        except Exception as e:
            logger.error(f"Failed to elaborate content for '{title}': {e}", exc_info=True)
            raise


def run_elaboration():
    """
    Fetches all documents, elaborates their content using an LLM,
    and updates them in the database.
    """
    logger.info("Starting documentation elaboration process...")
    
    try:
        elaborator = DocElaborator()
        documents = db_ops.get_docs()
    except Exception as e:
        logger.error(f"Failed to initialize or fetch documents: {e}", exc_info=True)
        return

    if not documents:
        logger.info("No documents found to elaborate.")
        return

    logger.info(f"Found {len(documents)} documents to process.")
    updated_count = 0

    for doc in documents:
        doc_id = doc['id']
        title = doc['title']
        original_content = doc['content']

        try:
            new_content = elaborator.elaborate_markdown(title, original_content)
            
            success = db_ops.update_document_content(doc_id, new_content)
            
            if success:
                logger.info(f"Successfully updated document: '{title}' (ID: {doc_id})")
                updated_count += 1
            else:
                logger.warning(f"Update for document '{title}' (ID: {doc_id}) failed.")

        except Exception as e:
            logger.error(f"Skipping document '{title}' (ID: {doc_id}) due to an error: {e}")
            continue

    logger.info(f"Documentation elaboration process finished. Updated {updated_count} documents.")


if __name__ == "__main__":
    run_elaboration() 