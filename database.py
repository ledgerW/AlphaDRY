from sqlmodel import SQLModel, Field, create_engine, Session, Relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from sqlalchemy import JSON, Column, Enum as SQLEnum, inspect
from schemas import Warpcast
from agents.multi_agent_alpha_scout import Chain
import time

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

class TokenOpportunityDB(SQLModel, table=True):
    """Database model for token investment opportunities"""
    __tablename__ = f"{get_env_prefix()}token_opportunities"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    chain: Chain = Field(sa_column=Column(SQLEnum(Chain)))
    contract_address: Optional[str]
    market_cap: Optional[float]
    community_score: int
    safety_score: int
    justification: str
    sources: List[str] = Field(sa_column=Column(JSON))
    
    # Relationship with AlphaReport
    report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}alpha_reports.id")
    report: Optional["AlphaReportDB"] = Relationship(back_populates="opportunities")

class AlphaReportDB(SQLModel, table=True):
    """Database model for alpha reports"""
    __tablename__ = f"{get_env_prefix()}alpha_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    is_relevant: bool
    analysis: str
    message: str  # Original message input
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship with TokenOpportunity
    opportunities: List[TokenOpportunityDB] = Relationship(back_populates="report")

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
        pulled_from_user: str = Field(index=True)

        @classmethod
        def from_warpcast(cls, warpcast: Warpcast, pulled_from_user: str) -> "WarpcastDB":
            return cls(
                raw_cast=warpcast.raw_cast,
                hash=warpcast.hash,
                username=warpcast.username,
                user_fid=warpcast.user_fid,
                text=warpcast.text,
                timestamp=warpcast.timestamp,
                replies=warpcast.replies,
                reactions=warpcast.reactions,
                recasts=warpcast.recasts,
                pulled_from_user=pulled_from_user
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

def tables_exist() -> bool:
    """Check if all required tables exist."""
    engine = get_engine()
    inspector = inspect(engine)
    env_prefix = get_env_prefix()
    required_tables = [
        f"{env_prefix}token_opportunities",
        f"{env_prefix}alpha_reports",
        f"{env_prefix}warpcasts"
    ]
    existing_tables = inspector.get_table_names()
    return all(table in existing_tables for table in required_tables)

def populate_dev_data():
    """Populate development tables with dummy data."""
    if get_env_prefix() != "dev_":
        return

    # Create alpha reports and opportunities in a separate transaction
    with get_session() as session:
        try:
            # Create a sample alpha report
            report = AlphaReportDB(
                is_relevant=True,
                analysis="This is a sample analysis of market opportunities",
                message="Sample input message"
            )
            session.add(report)
            session.flush()

            # Create sample token opportunities
            opportunities = [
                TokenOpportunityDB(
                    name="Sample Token 1",
                    chain=Chain.BASE,
                    contract_address="0x1234567890abcdef",
                    market_cap=1000000.0,
                    community_score=8,
                    safety_score=7,
                    justification="Strong community and solid fundamentals",
                    sources=["source1.com", "source2.com"],
                    report_id=report.id
                ),
                TokenOpportunityDB(
                    name="Sample Token 2",
                    chain=Chain.SOLANA,
                    contract_address="SOL123456789",
                    market_cap=500000.0,
                    community_score=6,
                    safety_score=8,
                    justification="Innovative technology with growing adoption",
                    sources=["source3.com", "source4.com"],
                    report_id=report.id
                )
            ]
            for opp in opportunities:
                session.add(opp)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating alpha reports: {e}")

    # Create warpcast data in a separate transaction
    with get_session() as session:
        try:
            Model = get_model()
            warpcast = Model(
                raw_cast={"sample": "data"},
                hash="sample_hash_123",
                username="test_user",
                user_fid=12345,
                text="This is a sample warpcast message",
                timestamp=datetime.utcnow(),
                replies=5,
                reactions=10,
                recasts=3,
                pulled_from_user="sample_puller"
            )
            session.add(warpcast)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating warpcast: {e}")

def reset_db():
    """Drop all tables and recreate them with fresh dummy data."""
    engine = get_engine()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    populate_dev_data()

def create_db_and_tables(force_reset: bool = False):
    """Create database tables if they don't exist and populate dev data."""
    if force_reset:
        reset_db()
    elif not tables_exist():
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        populate_dev_data()

def get_session():
    """Get a new database session."""
    return Session(get_engine())

def create_warpcast(warpcast: Warpcast, pulled_from_user: str) -> Optional[Any]:
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
                
            db_warpcast = Model.from_warpcast(warpcast, pulled_from_user)
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

def create_alpha_report(report_data: Dict[str, Any]) -> Optional[AlphaReportDB]:
    """Create a new alpha report with its associated token opportunities."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            with get_session() as session:
                # Create the report
                report = AlphaReportDB(
                    is_relevant=report_data["is_relevant"],
                    analysis=report_data["analysis"],
                    message=report_data.get("message", "")  # Get message from report data
                )
                session.add(report)
                session.flush()  # Flush to get the report ID

                # Create associated opportunities
                for opp_data in report_data["opportunities"]:
                    opportunity = TokenOpportunityDB(
                        report_id=report.id,
                        **opp_data
                    )
                    session.add(opportunity)

                session.commit()
                session.refresh(report)
                return report
                
        except Exception as e:
            print(f"Error creating alpha report (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None

def get_alpha_report(report_id: int) -> Optional[AlphaReportDB]:
    """Get an alpha report by ID."""
    with get_session() as session:
        return session.get(AlphaReportDB, report_id)

def get_all_alpha_reports() -> List[AlphaReportDB]:
    """Get all alpha reports."""
    with get_session() as session:
        return session.query(AlphaReportDB).all()

if __name__ == "__main__":
    create_db_and_tables()
