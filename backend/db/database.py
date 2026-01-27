"""
Database Configuration

Handles database connections and session management.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./test.db"  # Use SQLite for testing and development
)

# Create engine - optimized for performance
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False  # Required for SQLite

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency to get database session - optimized for large scale"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with migrations instead of direct table creation"""
    from alembic import command
    from alembic.config import Config

    # Configure Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    try:
        # Run migrations to latest version
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Fallback to create_all for development if migrations fail
        if DATABASE_URL.startswith("sqlite"):
            logger.warning(
                "Falling back to direct table creation for SQLite development"
            )
            from backend.db import models

            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized with create_all (development mode)")
        else:
            raise
