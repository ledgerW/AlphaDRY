from .base import *

class SocialMediaPostDB(SQLModel, table=True):
    """Database model for social media posts"""
    __tablename__ = f"{get_env_prefix()}social_media_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # e.g. "warpcast", "twitter", etc.
    post_id: str = Field(unique=True)  # Original post ID/hash from the source
    author_id: str = Field(index=True)  # Author's ID in the source platform
    author_username: str = Field(index=True)
    author_display_name: Optional[str]
    text: str
    original_timestamp: datetime  # Original post date/time from the source platform
    timestamp: datetime  # When we processed the post
    reactions_count: int = Field(default=0)
    replies_count: int = Field(default=0)
    reposts_count: int = Field(default=0)
    raw_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship with TokenReport
    token_report_id: Optional[int] = Field(default=None, foreign_key=f"{get_env_prefix()}token_reports.id")
    token_report: Optional["TokenReportDB"] = Relationship(back_populates="social_media_post")

class TokenReportDB(SQLModel, table=True):
    """Database model for token reports"""
    __tablename__ = f"{get_env_prefix()}token_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    mentions_purchasable_token: bool
    token_symbol: Optional[str]
    token_chain: Optional[str]
    token_address: Optional[str]
    is_listed_on_dex: Optional[bool]
    trading_pairs: List[str] = Field(sa_column=Column(JSON), default=[])
    confidence_score: int
    reasoning: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship with SocialMediaPost
    social_media_post: Optional[SocialMediaPostDB] = Relationship(back_populates="token_report")
    
    # Relationship with TokenOpportunity
    opportunities: List["TokenOpportunityDB"] = Relationship(back_populates="token_report")
