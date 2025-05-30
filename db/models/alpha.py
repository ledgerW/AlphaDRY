from .base import *
from agents.models import Chain
from pydantic import validator
from sqlalchemy import String, Integer, Sequence
from .social import TokenReportDB
from .token import TokenDB

class TokenOpportunityDB(SQLModel, table=True):
    """Database model for token investment opportunities"""
    __tablename__ = f"{get_env_prefix()}token_opportunities"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    chain: Chain = Field(sa_column=Column(String, nullable=False))  # Store as string to use enum value
    contract_address: Optional[str]
    market_cap: Optional[float]
    community_score: int
    safety_score: int
    justification: str
    sources: List[str] = Field(sa_column=Column(JSON))
    recommendation: str = Field(default="Hold")  # Buy/Hold/Sell recommendation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship with AlphaReport
    report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}alpha_reports.id")
    report: Optional["AlphaReportDB"] = Relationship(back_populates="opportunities")

    # Relationship with TokenReport
    token_report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}token_reports.id")
    token_report: Optional["TokenReportDB"] = Relationship(back_populates="opportunities")
    
    # Relationship with Token
    token_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}tokens.id")
    token: Optional["TokenDB"] = Relationship(back_populates="token_opportunities")

    @validator('chain', pre=True)
    def validate_chain(cls, v):
        if isinstance(v, Chain):
            return v.value  # Use the enum value (lowercase string)
        return v
        
    @validator('contract_address', pre=True)
    def validate_contract_address(cls, v):
        if v is not None:
            return v.lower()
        return v

class AlphaReportDB(SQLModel, table=True):
    """Database model for alpha reports"""
    __tablename__ = f"{get_env_prefix()}alpha_reports"

    id: Optional[int] = Field(
        sa_column=Column(
            Integer,
            Sequence(f'{get_env_prefix()}alpha_reports_id_seq'),
            primary_key=True,
            nullable=False
        )
    )
    is_relevant: bool
    analysis: str
    message: str  # Original message input
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship with TokenOpportunity
    opportunities: List[TokenOpportunityDB] = Relationship(back_populates="report")
