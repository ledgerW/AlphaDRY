from .base import *
from schemas import Warpcast

# Global model cache
_model_cache = {}

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
