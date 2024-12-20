from .base import *
from agents.models import Chain

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
    recommendation: str = Field(default="Hold")  # Buy/Hold/Sell recommendation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship with AlphaReport
    report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}alpha_reports.id")
    report: Optional["AlphaReportDB"] = Relationship(back_populates="opportunities")

    # Relationship with TokenReport
    token_report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}token_reports.id")
    token_report: Optional["TokenReportDB"] = Relationship(back_populates="opportunities")

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
