"""
Dependency injection utilities for the application.
"""
from __future__ import annotations
from typing import Optional
from app.db.repository import SessionLocal
from app.settings import settings

def get_db_session():
    """Get database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_settings():
    """Get application settings."""
    return settings
