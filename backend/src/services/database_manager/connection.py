import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Singleton pattern for the engine
_engine: Engine | None = None
_session_maker: sessionmaker[Session] | None = None


def get_db_connection_string(driver: str = "psycopg") -> str:
    """
    Constructs the database connection string from environment variables.
    """
    password = os.getenv("PG_PASSWORD")
    user = os.getenv("PG_USER")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    dbname = os.getenv("PG_DB")

    if not all([user, host, port, dbname]):
        raise ValueError(
            "Database connection variables (PG_USER, PG_HOST, PG_PORT, PG_DB) are not fully set."
        )

    user_info = user or ""
    if password:
        user_info += f":{password}"

    return f"postgresql+{driver}://{user_info}@{host}:{port}/{dbname}"


def get_engine() -> Engine:
    """
    Establishes a connection to the PostgreSQL database and returns a SQLAlchemy Engine.
    Uses a singleton pattern to ensure only one engine is created.
    """
    global _engine
    if _engine is None:
        try:
            db_url = get_db_connection_string()
            _engine = create_engine(db_url)

            # Test connection to ensure it's valid
            with _engine.connect() as connection:
                print("Database engine created and connection successful.")

        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    return _engine


def get_db_session() -> Session:
    """
    Returns a new database session from a session maker.
    Initializes the session maker if it hasn't been already.
    """
    global _session_maker
    if _session_maker is None:
        engine = get_engine()
        _session_maker = sessionmaker(bind=engine)

    return _session_maker() 