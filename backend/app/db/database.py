import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

logger = logging.getLogger("dentalai.db")

POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://dentalai:dentalai_password@localhost:5432/dentalai")
SQLITE_FALLBACK_URL = "sqlite:///./dentalai.db"

def get_engine():
    # Attempt connecting to primary configured DB (PostgreSQL)
    try:
        engine = create_engine(
            POSTGRES_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3} if "postgresql" in POSTGRES_URL else {}
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to primary database: PostgreSQL")
        return engine
    except Exception as e:
        logger.warning(
            "Primary database connection failed (%s). Falling back seamlessly to local SQLite database (%s).",
            e, SQLITE_FALLBACK_URL
        )
        sqlite_engine = create_engine(
            SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes schema tables if not existing."""
    logger.info("Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

