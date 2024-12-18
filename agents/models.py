from typing import Annotated, Optional, Sequence, List, Dict, Literal
from pydantic import BaseModel, Field
from enum import Enum
from typing_extensions import TypedDict


# Models
class Chain(str, Enum):
    BASE = 'Base'
    SOLANA = 'Solana'
    DEGEN = 'Degen'
    ETHEREUM = 'Ethereum'


class TokenAlpha(BaseModel):
    """Details about a potential token investment opportunity"""
    name: str = Field(description="Name of the token")
    chain: Chain = Field(description="The blockchain the token is on (Base or Solana)")
    contract_address: Optional[str] = Field(description="Contract address of the token if available")
    market_cap: Optional[float] = Field(description="fdv_usd value in Token Data, if available, or market cap in USD")
    community_score: int = Field(description="Score from 1-10 rating the strength and reputation of the community")
    safety_score: int = Field(description="Score from 1-10 rating the safety of the contract and team")
    justification: str = Field(description="Detailed explanation of why this token is a good opportunity")
    sources: List[str] = Field(description="URLs or references supporting the analysis")
    recommendation: Annotated[
        Literal["Buy", "Hold", "Sell"],
        "The recommended action to take on this token"
    ]


class TransactionData(BaseModel):
    fdv_usd: Optional[float] = Field(description="Fully diluted value in USD")
    market_cap_usd: Optional[float] = Field(description="Market cap in USD")
    price_change_5m: Optional[float] = Field(description="5 minute price change percentage")
    price_change_1h: Optional[float] = Field(description="1 hour price change percentage") 
    price_change_6h: Optional[float] = Field(description="6 hour price change percentage")
    price_change_24h: Optional[float] = Field(description="24 hour price change percentage")
    transactions_1h: Optional[dict] = Field(description="1 hour transaction counts")
    transactions_24h: Optional[dict] = Field(description="24 hour transaction counts")
    volume_1h: Optional[float] = Field(description="1 hour volume in USD")
    volume_24h: Optional[float] = Field(description="24 hour volume in USD")
    reserve_in_usd: Optional[float] = Field(description="Total reserve in USD")


class TokenData(BaseModel):
    chain: str
    address: str
    name: str
    symbol: str
    attributes: dict
    transaction_data: Optional[TransactionData] = None
