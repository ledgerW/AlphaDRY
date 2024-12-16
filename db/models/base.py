from sqlmodel import SQLModel, Field, Session, Relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import JSON, Column, Enum as SQLEnum
from ..connection import get_engine, get_env_prefix

def get_session():
    """Get a new database session."""
    return Session(get_engine())
