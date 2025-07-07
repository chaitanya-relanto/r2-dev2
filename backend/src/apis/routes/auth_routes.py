from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.database_manager import operations as db_ops
from src.utils.logger import get_logger

# --- Setup ---
router = APIRouter()
logger = get_logger(__name__)

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's password (plaintext).")

class UserResponse(BaseModel):
    user_id: str
    name: str
    role: str

class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    role: str

# --- API Endpoints ---
@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest):
    """
    Authenticate a user and return their details upon successful login.
    """
    log_extra = {"email": request.email}
    logger.info("Login attempt received.", extra=log_extra)

    try:
        user = db_ops.get_user_by_email_for_auth(request.email)

        if not user or user['password'] != request.password:
            logger.warning("Invalid email or password.", extra=log_extra)
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        logger.info("Login successful.", extra=log_extra)
        return UserResponse(
            user_id=user['id'],
            name=user['name'],
            role=user['role']
        )
    except Exception as e:
        logger.error(f"An error occurred during login: {e}", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@router.get("/users", response_model=List[UserSchema])
def get_all_users():
    """
    Get a list of all users in the database (for debugging).
    """
    try:
        users_data = db_ops.get_all_users()
        return [UserSchema(**user) for user in users_data]
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch users.") 