import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.ext.declarative import declarative_base

from src.utils.database import get_engine
from src.utils.logger import get_logger

# --- Setup ---
router = APIRouter()
logger = get_logger(__name__)

# --- SQLAlchemy Setup ---
Base = declarative_base()
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Model ---
class User(Base):
    __tablename__ = 'users'
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String) # For now, plaintext
    role = Column(String, nullable=False)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's password (plaintext).")

class UserResponse(BaseModel):
    user_id: uuid.UUID = Field(..., description="User's unique ID.")
    name: str = Field(..., description="User's name.")
    role: str = Field(..., description="User's role (e.g., developer, admin).")

class UserListResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    class Config:
        from_attributes = True

# --- API Endpoints ---
@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return their details upon successful login.
    """
    log_extra = {"email": request.email}
    logger.info("Login attempt received.", extra=log_extra)

    try:
        user: User | None = db.query(User).filter(User.email == request.email).first()

        if user is None or user.password != request.password:
            logger.warning("Invalid email or password.", extra=log_extra)
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        logger.info("Login successful.", extra=log_extra)
        return UserResponse(
            user_id=user.id,
            name=user.name,
            role=user.role
        )
    except Exception as e:
        logger.error(f"An error occurred during login: {e}", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@router.get("/users", response_model=List[UserListResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Get a list of all users in the database (for debugging).
    """
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch users.") 