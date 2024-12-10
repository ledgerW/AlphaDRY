from typing import Annotated, Optional, Sequence, List, Dict
from pydantic import BaseModel, Field
from enum import Enum
from typing_extensions import TypedDict


# Models
class Chain(str, Enum):
    BASE = 'Base'
    SOLANA = 'Solana'


class TokenOpportunity(BaseModel):
    """Details about a potential token investment opportunity"""
    name: str = Field(description="Name of the token")
    chain: Chain = Field(description="The blockchain the token is on (Base or Solana)")
    contract_address: Optional[str] = Field(description="Contract address of the token if available")
    market_cap: Optional[float] = Field(description="fdv_usd value in Token Data, if available, or market cap in USD")
    community_score: int = Field(description="Score from 1-10 rating the strength and reputation of the community")
    safety_score: int = Field(description="Score from 1-10 rating the safety of the contract and team")
    justification: str = Field(description="Detailed explanation of why this token is a good opportunity")
    sources: List[str] = Field(description="URLs or references supporting the analysis")


class AlphaReport(BaseModel):
    """Final report of token opportunities"""
    is_relevant: bool = Field(description="Whether the input messages are relevant to token opportunities")
    opportunities: List[TokenOpportunity] = Field(description="List of identified token opportunities")
    analysis: str = Field(description="Overall analysis and summary of the opportunities")


class TokenData(BaseModel):
    chain: str
    address: str
    name: str
    symbol: str
    attributes: Dict
