from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import time

from src.services.recommendation_engine.service import RecommendationService
from src.utils.logger import get_logger

# --- Setup ---
router = APIRouter()
logger = get_logger(__name__)

# Initialize the RecommendationService globally to reuse the instance
try:
    recommendation_service = RecommendationService()
    logger.info("RecommendationService initialized successfully for API router.")
except Exception as e:
    logger.error(f"Fatal error initializing RecommendationService for API: {e}", exc_info=True)
    recommendation_service = None

# --- Pydantic Models ---
class RecommendationRequest(BaseModel):
    session_id: str = Field(..., description="The session ID to analyze for recommendations.")
    num_messages: Optional[int] = Field(10, description="Number of recent messages to consider (default: 10).", ge=1, le=50)

class RecommendationResponse(BaseModel):
    suggestions: List[str] = Field(..., description="List of 2-3 follow-up action recommendations.")
    session_id: str = Field(..., description="The session ID that was analyzed.")
    status: str = Field("success", description="The status of the request.")
    duration_seconds: float = Field(..., description="Time taken to generate recommendations in seconds.")

# --- API Endpoints ---
@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Generate 2-3 follow-up action recommendations based on recent chat messages in a session.
    
    This endpoint analyzes the most recent messages in a chat session and uses AI to suggest
    relevant follow-up actions that the user might want to take next.
    """
    if not recommendation_service:
        logger.error("RecommendationService is not available. The application failed to start correctly.")
        raise HTTPException(status_code=500, detail="Recommendation service is currently unavailable.")

    try:
        log_extra = {"session_id": request.session_id}
        logger.info(f"Received recommendation request for session {request.session_id} with {request.num_messages} messages.", extra=log_extra)

        start_time = time.time()

        # Generate recommendations using the service
        suggestions = recommendation_service.generate_recommendations(
            session_id=request.session_id,
            num_messages=request.num_messages or 10
        )

        duration = time.time() - start_time
        logger.info(f"Generated {len(suggestions)} recommendations in {duration:.2f} seconds.", extra=log_extra)

        return RecommendationResponse(
            suggestions=suggestions,
            session_id=request.session_id,
            status="success",
            duration_seconds=duration
        )

    except Exception as e:
        logger.error(f"An error occurred during recommendation generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}") 