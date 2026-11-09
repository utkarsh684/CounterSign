"""Database session management with SQLAlchemy 2.0.

Provides sessionmaker, engine lifecycle, and FastAPI dependency.
Gracefully falls back to local SQLite if MySQL credentials are not yet configured or reachable.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

database_url = settings.DATABASE_URL

# For MySQL, ensure charset is utf8mb4
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        database_url,
        echo=settings.SQL_ECHO,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    # Test connection
    with engine.connect() as conn:
        logger.info(f"Database connection established successfully to {database_url.split('@')[-1] if '@' in database_url else database_url}")
except Exception as e:
    logger.warning(f"Could not connect to configured database at {database_url}: {e}. Initializing local fallback database.")
    database_url = "sqlite:///./countersign.db"
    engine = create_engine(
        database_url,
        echo=settings.SQL_ECHO,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields an independent database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
