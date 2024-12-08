from sqlmodel import SQLModel, Field, create_engine, Session, select
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from sqlalchemy import JSON, Column, text, MetaData, Table
from schemas import Warpcast

load_dotenv()

# Global variables for database connection
_engine = None
_current_schema = None

def get_schema() -> str:
    """Get the current schema based on environment."""
    is_deployed = os.getenv("REPLIT_DEPLOYMENT") == "1"
    return "prod" if is_deployed else "dev"

def get_engine():
    """Get or create SQLAlchemy engine with proper schema."""
    global _engine, _current_schema
    
    new_schema = get_schema()
    
    # If schema has changed or engine doesn't exist, create new engine
    if _engine is None or new_schema != _current_schema:
        # Dispose of old engine if it exists
        if _engine is not None:
            _engine.dispose()
        
        # Create new engine
        _current_schema = new_schema
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
            
        _engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=new_schema == "dev"  # Enable SQL logging in development environment
        )
    
    return _engine

# Create SQLModel for Warpcast
class WarpcastDB(SQLModel, table=True):
    __tablename__ = "warpcasts"
    
    # Set schema and table constraints
    __table_args__ = (
        {'schema': get_schema()}
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_cast: Dict[str, Any] = Field(sa_column=Column(JSON))
    hash: str = Field(unique=True)
    username: str = Field(index=True)
    user_fid: int = Field(index=True)
    text: str
    timestamp: datetime
    replies: int
    reactions: int
    recasts: int

    @classmethod
    def from_warpcast(cls, warpcast: Warpcast) -> "WarpcastDB":
        return cls(
            raw_cast=warpcast.raw_cast,
            hash=warpcast.hash,
            username=warpcast.username,
            user_fid=warpcast.user_fid,
            text=warpcast.text,
            timestamp=warpcast.timestamp,
            replies=warpcast.replies,
            reactions=warpcast.reactions,
            recasts=warpcast.recasts
        )

    def to_warpcast(self) -> Warpcast:
        return Warpcast(
            raw_cast=self.raw_cast,
            hash=self.hash,
            username=self.username,
            user_fid=self.user_fid,
            text=self.text,
            timestamp=self.timestamp,
            replies=self.replies,
            reactions=self.reactions,
            recasts=self.recasts
        )

def create_db_and_tables():
    """Create schema and all database tables. Safe to call on startup."""
    engine = get_engine()
    schema = get_schema()
    
    # Create schema if it doesn't exist
    with engine.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        connection.commit()
        
        # Create table with explicit schema reference
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.warpcasts (
            id SERIAL PRIMARY KEY,
            raw_cast JSONB,
            hash VARCHAR UNIQUE,
            username VARCHAR,
            user_fid INTEGER,
            text TEXT,
            timestamp TIMESTAMP,
            replies INTEGER,
            reactions INTEGER,
            recasts INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_{schema}_warpcasts_username ON {schema}.warpcasts (username);
        CREATE INDEX IF NOT EXISTS idx_{schema}_warpcasts_user_fid ON {schema}.warpcasts (user_fid);
        """
        connection.execute(text(create_table_sql))
        connection.commit()

def get_session():
    """Get a new database session using the current schema."""
    return Session(get_engine())

def create_warpcast(warpcast: Warpcast) -> Optional[WarpcastDB]:
    """
    Create a new warpcast entry if it doesn't exist.
    Returns None if a warpcast with the same hash already exists.
    """
    with get_session() as session:
        try:
            # Check if warpcast already exists
            existing = session.exec(
                select(WarpcastDB).where(WarpcastDB.hash == warpcast.hash)
            ).first()
            
            if existing:
                return None
                
            db_warpcast = WarpcastDB.from_warpcast(warpcast)
            session.add(db_warpcast)
            session.commit()
            session.refresh(db_warpcast)
            return db_warpcast
        except Exception as e:
            session.rollback()
            print(f"Error creating warpcast: {e}")
            return None

def get_warpcast_by_hash(hash: str) -> Optional[Warpcast]:
    with get_session() as session:
        statement = select(WarpcastDB).where(WarpcastDB.hash == hash)
        db_warpcast = session.exec(statement).first()
        return db_warpcast.to_warpcast() if db_warpcast else None

def get_warpcasts_by_username(username: str) -> List[Warpcast]:
    with get_session() as session:
        statement = select(WarpcastDB).where(WarpcastDB.username == username)
        db_warpcasts = session.exec(statement).all()
        return [cast.to_warpcast() for cast in db_warpcasts]

def get_all_warpcasts() -> List[Warpcast]:
    with get_session() as session:
        statement = select(WarpcastDB)
        db_warpcasts = session.exec(statement).all()
        return [cast.to_warpcast() for cast in db_warpcasts]

if __name__ == "__main__":
    create_db_and_tables()
