from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
import os

load_dotenv()

# Global variables for database connection
_engine = None
_env_prefix = None

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
            pool_pre_ping=True,  # Enable connection health checks
            connect_args={
                "connect_timeout": 10,  # Connection timeout in seconds
                "keepalives": 1,        # Enable keepalive
                "keepalives_idle": 30,  # Idle time before sending keepalive
                "keepalives_interval": 10,  # Interval between keepalives
                "keepalives_count": 5    # Number of keepalive retries
            },
            echo=_env_prefix.startswith("dev_")  # Enable SQL logging in development environment
        )
    
    return _engine

def tables_exist() -> bool:
    """Check if all required tables exist."""
    engine = get_engine()
    inspector = inspect(engine)
    env_prefix = get_env_prefix()
    required_tables = [
        f"{env_prefix}token_opportunities",
        f"{env_prefix}alpha_reports",
        f"{env_prefix}warpcasts",
        f"{env_prefix}social_media_posts",
        f"{env_prefix}token_reports"
    ]
    existing_tables = inspector.get_table_names()
    return all(table in existing_tables for table in required_tables)
