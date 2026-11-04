"""
Database connection management for Flood Prediction and Decision Support System.
Supports PostgreSQL (production) with automatic fallback to SQLite (development).
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import BASE_DIR

# Database URL from environment or default to SQLite file in data directory
DEFAULT_DB_PATH = BASE_DIR / "data" / "flood_system.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Configure SQLite specifically for multi-threaded FastAPI access
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes tables and seeds initial station metadata from station_lookup.csv and cwc_thresholds.csv."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
