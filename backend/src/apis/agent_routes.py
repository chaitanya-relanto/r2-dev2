from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import uuid
from typing import Optional
import time

from src.services.agent.chat import ChatAgent
from src.utils.logger import get_logger

# --- Setup ---
router = APIRouter()
logger = get_logger(__name__)

# Initialize the ChatAgent globally to reuse the instance
# This avoids re-initializing the agent and its models on every request.
try:
    agent = ChatAgent()
    logger.info("ChatAgent initialized successfully for API router.")
except Exception as e:
    logger.error(f"Fatal error initializing ChatAgent for API: {e}", exc_info=True)
    agent = None

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: str = Field(..., description="The user's query for the agent.")
    session_id: Optional[str] = Field(None, description="Optional session ID to maintain conversation context.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The final string response from the agent.")
    session_id: str = Field(..., description="The session ID used for tracking the conversation.")
    status: str = Field("success", description="The status of the request.")
    duration_seconds: float = Field(..., description="Time taken to process the request in seconds.")

# --- API Endpoint ---
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Interact with the LangGraph-based developer assistant.
    """
    if not agent:
        logger.error("ChatAgent is not available. The application failed to start correctly.")
        raise HTTPException(status_code=500, detail="Agent service is currently unavailable.")

    session_id = request.session_id or str(uuid.uuid4())
    log_extra = {"user_id": request.user_id, "session_id": session_id}

    logger.info(f"Received chat request with query: '{request.query}'", extra=log_extra)

    try:
        start_time = time.time()

        # Run the agent with the provided details
        final_response = agent.run(
            user_query=request.query,
            user_id=request.user_id,
            session_id=session_id
        )

        duration = time.time() - start_time
        logger.info(f"Agent generated response successfully in {duration:.2f} seconds.", extra=log_extra)

        return ChatResponse(
            response=final_response,
            session_id=session_id,
            status="success",
            duration_seconds=duration
        )

    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}") 