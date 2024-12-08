from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Any, Union, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from dateutil import parser
import json


# Warpcast
class Warpcast(BaseModel):
    raw_cast: Annotated[dict[str, Any], "Raw cast data from the Farcaster API"]
    hash: Annotated[str, "Unique identifier hash of the cast"]
    username: Annotated[str, "Username of the cast author"]
    user_fid: Annotated[int, "Farcaster ID (FID) of the cast author"]
    text: Annotated[str, "Content text of the cast"]
    timestamp: Annotated[datetime, "Timestamp of when the cast was created"]
    replies: Annotated[int, "Number of replies to this cast"]
    reactions: Annotated[int, "Number of reactions (likes) on this cast"]
    recasts: Annotated[int, "Number of times this cast was recasted"]

    @classmethod
    def from_cast(cls, cast: dict[str, Any]) -> "Warpcast":
        return cls(
            raw_cast=cast,
            hash=cast['hash'],
            username=cast['author']['username'],
            user_fid=cast['author']['fid'],
            text=cast['text'],
            timestamp=datetime.fromtimestamp(cast['timestamp']/1000),
            replies=cast['replies']['count'],
            reactions=cast['reactions']['count'],
            recasts=cast['recasts']['count']
        )
