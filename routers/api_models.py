from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TokenData(BaseModel):
    symbol: str
    name: str
    chain: str
    address: Optional[str] = None
    image_url: Optional[str] = None
    website_url: Optional[str] = None
    warpcast_url: Optional[str] = None
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    signal_url: Optional[str] = None

class TokenOpportunity(BaseModel):
    name: str
    chain: str
    contract_address: Optional[str] = None
    market_cap: Optional[float] = None
    community_score: Optional[int] = None
    safety_score: Optional[int] = None
    justification: str
    sources: List[str]
    recommendation: str
    created_at: datetime
    token: Optional[TokenData] = None
    token_report: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AlphaReport(BaseModel):
    id: int
    is_relevant: bool
    analysis: str
    message: str
    created_at: datetime
    opportunities: List[TokenOpportunity]

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class Token(BaseModel):
    name: str
    symbol: str
    chain: str

    def __str__(self):
        return f"Token(name={self.name}, symbol={self.symbol}, chain={self.chain})"

class SocialMediaInput(BaseModel):
    """Input model for social media text analysis"""
    text: str = Field(..., description="The social media post text to analyze")
    source: str = Field(default="unknown", description="Source platform of the post")
    author_id: str = Field(default="unknown", description="Author's ID in the source platform")
    author_username: str = Field(default="unknown", description="Author's username")
    author_display_name: str = Field(default=None, description="Author's display name")
    post_id: str = Field(default=None, description="Original post ID from the source")
    original_timestamp: datetime = Field(default=None, description="Original post date/time from the source platform")
    reactions_count: int = Field(default=0, description="Number of reactions to the post")
    replies_count: int = Field(default=0, description="Number of replies to the post")
    reposts_count: int = Field(default=0, description="Number of reposts of the post")
