from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.apis.routes.data_routes import router as data_router
from src.apis.routes.chat_routes import router as chat_router
from src.apis.routes.auth_routes import router as auth_router
from src.apis.routes.recommendation_routes import router as recommendation_router
from src.utils.logger import get_logger

# --- Setup ---
logger = get_logger(__name__)

app = FastAPI(
    title="AI Developer Productivity Assistant API",
    description="API endpoints for serving mock data for the assistant.",
    version="0.1.0",
)

# --- CORS Middleware ---
# In a production app, you would want to be more restrictive with the allowed origins.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Welcome Message Function ---
def print_welcome_message():
    """Logs the ASCII art welcome message."""
    welcome_message = r"""
         _____  ___        _____            ___    ____             _                  _    _____ _             _           _ 
        |  __ \|__ \      |  __ \          |__ \  |  _ \           | |                | |  / ____| |           | |         | |
        | |__) |  ) |_____| |  | | _____   __ ) | | |_) | __ _  ___| | _____ _ __   __| | | (___ | |_ __ _ _ __| |_ ___  __| |
        |  _  /  / /______| |  | |/ _ \ \ / // /  |  _ < / _` |/ __| |/ / _ \ '_ \ / _` |  \___ \| __/ _` | '__| __/ _ \/ _` |
        | | \ \ / /_      | |__| |  __/\ V // /_  | |_) | (_| | (__|   <  __/ | | | (_| |  ____) | || (_| | |  | ||  __/ (_| |
        |_|  \_\____|     |_____/ \___| \_/|____| |____/ \__,_|\___|_|\_\___|_| |_|\__,_| |_____/ \__\__,_|_|   \__\___|\__,_|                                                                                                                                                                                                                          
            """
    # Use the configured logger to print the message
    logger.info(f"\n{welcome_message}\n") # Add newlines for better spacing in logs

# --- Startup Event Handler ---
@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup."""
    print_welcome_message()
    logger.info("FastAPI application startup complete.") # Optional: Log completion


# Include the data routes
app.include_router(data_router, prefix="/data", tags=["Data"])

# Include the agent routes
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

# Include the auth routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include the recommendation routes
app.include_router(recommendation_router, prefix="", tags=["Recommendations"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the R2-Dev2 API!"}
