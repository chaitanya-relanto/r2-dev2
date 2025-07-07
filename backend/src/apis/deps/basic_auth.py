import os
import secrets
from typing import cast
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

security = HTTPBasic()

# --- Environment Credentials ---
# Fetch credentials from environment variables for security
BASIC_AUTH_USER = os.getenv("BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.getenv("BASIC_AUTH_PASS")

if not all([BASIC_AUTH_USER, BASIC_AUTH_PASS]):
    raise ValueError(
        "BASIC_AUTH_USER and BASIC_AUTH_PASS must be set in your environment for authentication to work."
    )

def basic_auth_dependency(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    A reusable dependency for Basic Authentication.
    
    It compares the provided credentials against environment variables in a secure way.
    
    Usage:
        @router.post("/some-protected-route")
        def protected_route(user: str = Depends(basic_auth_dependency)):
            # `user` will be the authenticated username.
            # If authentication fails, a 401 error will be raised automatically.
            ...
            
    Testing with cURL:
        curl -X POST http://localhost:8000/some-protected-route \\
             -u "your_username:your_password" \\
             -H "Content-Type: application/json" \\
             -d '{"key": "value"}'
    """
    correct_user = secrets.compare_digest(credentials.username, cast(str, BASIC_AUTH_USER))
    correct_pass = secrets.compare_digest(credentials.password, cast(str, BASIC_AUTH_PASS))
    
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username 