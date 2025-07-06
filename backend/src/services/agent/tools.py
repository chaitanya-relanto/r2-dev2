from langchain_core.tools import tool
from sqlalchemy import text
from dotenv import load_dotenv

from src.services.database_manager.connection import get_db_session
from src.services.pr_summarizer.summarize import PRSummarizer
from src.services.doc_search.search import VectorSearchService
from src.utils.logger import get_logger

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")
logger = get_logger(__name__)

# --- Service Instantiation ---
try:
    vector_search_service = VectorSearchService()
    pr_summarizer = PRSummarizer()
    logger.info("Tool services initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize tool services: {e}", exc_info=True)
    vector_search_service = None
    pr_summarizer = None

# --- Tool Definitions ---

@tool
def pr_diff_tool(pr_id: str, user_id: str) -> str:
    """
    Retrieves the raw text of all git diffs associated with a Pull Request ID.
    The user_id is received but not currently used for access control on diffs.
    """
    logger.info(f"Executing PR diff tool for ID: {pr_id}")
    session = get_db_session()
    try:
        stmt = text("SELECT diff_text FROM git_diffs WHERE pr_id = :pr_id")
        results = session.execute(stmt, {"pr_id": pr_id}).fetchall()
        
        if not results:
            return f"Error: No diffs found for PR with ID {pr_id}."
            
        return "\\n---_---_---\\n".join([r[0] for r in results])
    except Exception as e:
        logger.error(f"Error in pr_diff_tool for {pr_id}: {e}", exc_info=True)
        return "An error occurred during PR diff retrieval."
    finally:
        session.close()

@tool
def pr_summary_tool(diff_text: str, user_id: str) -> str:
    """
    Summarizes the raw text of one or more git diffs.
    The user_id is received but not currently used.
    """
    logger.info(f"Executing PR summary tool for diff of length: {len(diff_text)}")
    if not pr_summarizer:
        return "Error: PR Summarizer service is not available."
    return pr_summarizer.summarize_diff(diff_text)

@tool
def doc_search_tool(query: str, user_id: str) -> str:
    """
    Searches the official documentation vector store for technical questions.
    The user_id is received but not currently used as documentation is public.
    """
    logger.info(f"Executing documentation search for query: '{query}'")
    if not vector_search_service:
        return "Error: Documentation Search service is not available."
    return vector_search_service.search_documentation(query)

@tool
def learning_search_tool(query: str, user_id: str) -> str:
    """
    Searches the internal learning database for curated insights, tutorials, and best practices.
    The user_id is received but not currently used as learning resources are public.
    """
    logger.info(f"Executing learning search for query: '{query}'")
    if not vector_search_service:
        return "Error: Learning Search service is not available."
    return vector_search_service.search_learnings(query) 