import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Singleton pattern for the engine
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Establishes a connection to the PostgreSQL database and returns a SQLAlchemy Engine.
    Uses a singleton pattern to ensure only one engine is created.
    """
    global _engine
    if _engine is None:
        try:
            password = os.getenv("PG_PASSWORD")
            user = os.getenv("PG_USER")
            host = os.getenv("PG_HOST")
            port = os.getenv("PG_PORT")
            dbname = os.getenv("PG_DB")

            if not all([user, host, port, dbname]):
                raise ValueError(
                    "Database connection variables (PG_USER, PG_HOST, PG_PORT, PG_DB) are not fully set."
                )

            if password:
                db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
            else:
                db_url = f"postgresql+psycopg://{user}@{host}:{port}/{dbname}"

            _engine = create_engine(db_url)

            # Test connection to ensure it's valid
            with _engine.connect() as connection:
                print("Database engine created and connection successful.")

        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    return _engine 