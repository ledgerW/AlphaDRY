from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from sqlalchemy import JSON, Column
from schemas import Warpcast

load_dotenv()

# Global variables for database connection
_engine = None
_env_prefix = None
_model_cache = {}

def get_env_prefix() -> str:
    """Get the current environment prefix for table names."""
    is_deployed = os.getenv("REPLIT_DEPLOYMENT") == "1"
    return "prod_" if is_deployed else "dev_"

def get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine, _env_prefix
    
    new_prefix = get_env_prefix()
    
    # If environment changed or engine doesn't exist, create new engine
    if _engine is None or new_prefix != _env_prefix:
        # Dispose of old engine if it exists
        if _engine is not None:
            _engine.dispose()
        
        # Create new engine
        _env_prefix = new_prefix
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
            
        _engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=_env_prefix.startswith("dev_")  # Enable SQL logging in development environment
        )
    
    return _engine

def create_warpcast_model(tablename: str):
    """Create a new WarpcastDB model with the specified table name."""
    class WarpcastDB(SQLModel, table=True):
        __tablename__ = tablename
        
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
    
    return WarpcastDB

def get_model():
    """Get the appropriate WarpcastDB model for the current environment."""
    global _model_cache
    
    env_prefix = get_env_prefix()
    if env_prefix not in _model_cache:
        tablename = f"{env_prefix}warpcasts"
        _model_cache[env_prefix] = create_warpcast_model(tablename)
    
    return _model_cache[env_prefix]

def create_db_and_tables():
    """Create all database tables. Safe to call on startup."""
    engine = get_engine()
    Model = get_model()
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    return Session(get_engine())

def create_warpcast(warpcast: Warpcast) -> Optional[Any]:
    """
    Create a new warpcast entry if it doesn't exist.
    Returns None if a warpcast with the same hash already exists.
    """
    Model = get_model()
    with get_session() as session:
        try:
            # Check if warpcast already exists
            existing = session.query(Model).filter(Model.hash == warpcast.hash).first()
            
            if existing:
                return None
                
            db_warpcast = Model.from_warpcast(warpcast)
            session.add(db_warpcast)
            session.commit()
            session.refresh(db_warpcast)
            return db_warpcast
        except Exception as e:
            session.rollback()
            print(f"Error creating warpcast: {e}")
            return None

def get_warpcast_by_hash(hash: str) -> Optional[Warpcast]:
    Model = get_model()
    with get_session() as session:
        db_warpcast = session.query(Model).filter(Model.hash == hash).first()
        return db_warpcast.to_warpcast() if db_warpcast else None

def get_warpcasts_by_username(username: str) -> List[Warpcast]:
    Model = get_model()
    with get_session() as session:
        db_warpcasts = session.query(Model).filter(Model.username == username).all()
        return [cast.to_warpcast() for cast in db_warpcasts]

def get_all_warpcasts() -> List[Warpcast]:
    Model = get_model()
    with get_session() as session:
        db_warpcasts = session.query(Model).all()
        return [cast.to_warpcast() for cast in db_warpcasts]

if __name__ == "__main__":
    create_db_and_tables()
