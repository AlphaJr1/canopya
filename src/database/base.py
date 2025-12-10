"""
Database configuration dan base setup
Mendukung PostgreSQL dan SQLite untuk development

"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Database URL dari environment variable atau default ke SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./aeropon.db"  # Default: SQLite untuk development
)

# Untuk PostgreSQL production, set environment variable:
# DATABASE_URL=postgresql://user:password@localhost/aeropon_db

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False  # Set True untuk debug SQL queries
    )
else:
    # PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk models
Base = declarative_base()

def get_db() -> Generator:
    """
    Dependency untuk mendapatkan database session
    
    Usage:
        from src.database import get_db
        db = next(get_db())
        try:
            # Use db
            pass
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database - create all tables
    
    Usage:
        from src.database.base import init_db
        from . import models  # Import models to register them
        init_db()
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {DATABASE_URL}")

def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")
