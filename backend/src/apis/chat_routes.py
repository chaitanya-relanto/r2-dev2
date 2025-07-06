from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import time
from datetime import datetime, timezone, timedelta

from src.services.database_manager import operations as db_ops

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
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="The role of the message sender.")
    message: str = Field(..., description="The content of the message.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=5, minutes=30))), description="The time the message was created.")


class ChatSession(BaseModel):
    session_id: str = Field(..., description="The unique identifier for the chat session.")
    title: str = Field(..., description="The title of the chat session.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=5, minutes=30))), description="The time the session was created.")

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    query: str = Field(..., description="The user's query for the agent.")
    session_id: Optional[str] = Field(None, description="Optional session ID to maintain conversation context.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The final string response from the agent.")
    session_id: str = Field(..., description="The session ID used for tracking the conversation.")
    status: str = Field("success", description="The status of the request.")
    duration_seconds: float = Field(..., description="Time taken to process the request in seconds.")

class SessionListResponse(BaseModel):
    sessions: List[ChatSession]

class MessageListResponse(BaseModel):
    messages: List[ChatMessage]

class RenameSessionRequest(BaseModel):
    new_title: str = Field(..., description="The new title for the chat session.")

# --- API Endpoint ---
@router.post("/agent", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Interact with the LangGraph-based developer assistant.
    """
    if not agent:
        logger.error("ChatAgent is not available. The application failed to start correctly.")
        raise HTTPException(status_code=500, detail="Agent service is currently unavailable.")

    try:
        session_id = request.session_id
        # If no session_id is provided, create a new session
        if not session_id:
            title = f"Session - {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S')}"
            session_id = db_ops.create_chat_session(user_id=request.user_id, title=title)
        
        history = db_ops.get_history(session_id) if session_id else []
        log_extra = {"user_id": request.user_id, "session_id": session_id}
        logger.info(f"Received chat request with query: '{request.query}'", extra=log_extra)

        # Store user message
        db_ops.store_message(session_id=session_id, user_id=request.user_id, role='user', message=request.query)

        start_time = time.time()

        # Run the agent with the provided details
        final_response = agent.run(
            user_query=request.query,
            user_id=request.user_id,
            session_id=session_id,
            history=history
        )

        duration = time.time() - start_time
        logger.info(f"Agent generated response successfully in {duration:.2f} seconds.", extra=log_extra)

        # Store agent response
        db_ops.store_message(session_id=session_id, user_id=request.user_id, role='assistant', message=final_response)

        return ChatResponse(
            response=final_response,
            session_id=session_id,
            status="success",
            duration_seconds=duration
        )

    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@router.get("/sessions/{user_id}", response_model=SessionListResponse)
async def get_sessions_for_user(user_id: str):
    """
    Retrieve all chat sessions for a given user.
    """
    try:
        sessions_data = db_ops.get_sessions(user_id=user_id)
        sessions = [ChatSession(**s) for s in sessions_data]
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions.")

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_messages_for_session(session_id: str):
    """
    Retrieve all messages for a given chat session.
    """
    try:
        messages_data = db_ops.get_messages(session_id=session_id)
        messages = [ChatMessage(**m) for m in messages_data]
        return MessageListResponse(messages=messages)
    except Exception as e:
        logger.error(f"Error fetching messages for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch chat messages.")

@router.put("/sessions/{session_id}/rename", status_code=204)
async def rename_session(session_id: str, request: RenameSessionRequest):
    """
    Rename a specific chat session.
    """
    try:
        success = db_ops.rename_chat_session(session_id, request.new_title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or title not updated.")
        return
    except Exception as e:
        logger.error(f"Error renaming session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rename chat session.")

@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """
    Delete a specific chat session and all its messages.
    """
    try:
        success = db_ops.delete_chat_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found.")
        return
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session.") 