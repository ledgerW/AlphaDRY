from .base import *
from agents.models import Chain
from pydantic import validator
from sqlalchemy import String, UniqueConstraint

class TokenDB(SQLModel, table=True):
    """Database model for unique tokens being tracked"""
    __tablename__ = f"{get_env_prefix()}tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    name: str
    chain: Chain = Field(sa_column=Column(String, nullable=False))
    address: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Social URLs
    image_url: Optional[str] = None
    website_url: Optional[str] = None
    warpcast_url: Optional[str] = None
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    signal_url: Optional[str] = None
    token_created_at: Optional[datetime] = None
    
    # Relationships
    token_reports: List["TokenReportDB"] = Relationship(back_populates="token")
    token_opportunities: List["TokenOpportunityDB"] = Relationship(back_populates="token")
    
    # Ensure uniqueness of token across chain and address
    __table_args__ = (
        UniqueConstraint('chain', 'address', name='uq_token_chain_address'),
    )
    
    @validator('chain', pre=True)
    def validate_chain(cls, v):
        if isinstance(v, Chain):
            return v.value
        return v
        
    @validator('address', pre=True)
    def validate_address(cls, v, values):
        if v is not None:
            # Only lowercase address for non-Solana chains
            chain = values.get('chain')
            if chain and chain.lower() != 'solana':
                return v.lower()
        return v
