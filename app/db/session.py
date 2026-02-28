"""
Database Session Configuration Module

This module handles database connection management using SQLAlchemy.
It provides session factory and dependency injection for FastAPI endpoints.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variable with fallback for development
# Using SQLite for development (no external DB required)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./smart_pharma.db"
)

# Check if using SQLite
is_sqlite = DATABASE_URL.startswith("sqlite")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True if not is_sqlite else False,
    echo=False            # Set to True for SQL query logging (debug)
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.
    
    This function creates a new database session for each request
    and automatically closes it when the request is completed.
    
    Yields:
        Session: SQLAlchemy database session instance.
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function should be called once at application startup
    to ensure all database tables exist.
    
    Note:
        In production, consider using Alembic for migrations
        instead of calling this function directly.
    """
    # Import models here to ensure they are registered with Base
    from app.db import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
