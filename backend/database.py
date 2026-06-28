"""
database.py
Sets up the SQLModel engine and provides a FastAPI dependency (get_db)
that yields a database session per-request.
"""
import os
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/multimodal_db"
)

# echo=False keeps logs clean; flip to True for local SQL debugging.
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all tables that don't already exist. Called once on app startup."""
    # Import models here so SQLModel's metadata registry knows about every table
    # before create_all() runs.
    from models import image, task, result  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_db():
    """FastAPI dependency: yields a session, closes it after the request."""
    with Session(engine) as session:
        yield session
