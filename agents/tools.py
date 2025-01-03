from langchain_core.tools import tool
from typing import List, Dict, Optional, Union, Annotated, Literal
from pydantic import BaseModel, Field
import requests

from agents.models import TokenData, TransactionData
from chains.tavily_chain import retriever as long_retriever, short_retriever

# Tools
@tool("quick_search")
def quick_search(query: str) -> List[dict]:
    """Do a quick initial web search for basic information."""
    docs = short_retriever.invoke(query)
    return [doc.dict() for doc in docs]


@tool("deep_search") 
def deep_search(query: str) -> List[dict]:
    """Do a detailed web search to gather more comprehensive information."""
    docs = long_retriever.invoke(query)
    return [doc.dict() for doc in docs]


def extract_token_transaction_data(attributes: dict) -> Optional[TransactionData]:
    """Extract transaction data from token attributes"""
    if not attributes:
        return None
        
    price_changes = attributes.get('price_change_percentage', {})
    return TransactionData(
        fdv_usd=float(attributes.get('fdv_usd', 0)),
        market_cap_usd=attributes.get('market_cap_usd'),
        price_change_5m=float(price_changes.get('m5', 0)),
        price_change_1h=float(price_changes.get('h1', 0)),
        price_change_6h=float(price_changes.get('h6', 0)),
        price_change_24h=float(price_changes.get('h24', 0)),
        transactions_1h=attributes.get('transactions', {}).get('h1'),
        transactions_24h=attributes.get('transactions', {}).get('h24'),
        volume_1h=float(attributes.get('volume_usd', {}).get('h1', 0)),
        volume_24h=float(attributes.get('volume_usd', {}).get('h24', 0)),
        reserve_in_usd=float(attributes.get('reserve_in_usd', 0))
    )

def extract_token_data(token_symbol: str, pool_data: dict) -> Optional[TokenData]:
    if not pool_data.get('data'):
        return None
        
    for pool in pool_data['data']:
        pool_name = pool['attributes']['name']
        chain = pool['relationships']['base_token']['data']['id'].split('_')[0]
        address = pool['relationships']['base_token']['data']['id'].split('_')[1]
        attributes = pool['attributes']
        
        # Extract symbol from pool name (e.g. "CLANKER / WETH 1%" -> "CLANKER")
        symbol = pool_name.split('/')[0].strip()
        if token_symbol.lower() in [symbol.lower(), address.lower()]:
            break
    else:
        # Loop completed without finding a match
        return None
        
    transaction_data = extract_token_transaction_data(attributes)
    
    return TokenData(
        chain=chain,
        address=address,
        name='',
        symbol=symbol,
        attributes=attributes,
        transaction_data=transaction_data
    )


def search_tokens(
        token_symbol: Annotated[str, "The symbol of a cryptocurrency token to search for"]
    ) -> dict:
    """
    Search for crypto tokens on GeckoTerminal and get the token data.
    """
    url = f"https://api.geckoterminal.com/api/v2/search/pools"
    headers = {"accept": "application/json"}
    params = {"query": token_symbol, "page": 1}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()


@tool("get_token_data")
def get_token_data(
        token: Annotated[str, "The symbol or address of the crypto token to search for"]
    ) -> Union[TokenData, None]:
    """
    Do a detailed crypto token search on GeckoTerminal to get financial, trading, and DEX data for the token.
    Use this tool when you have a token symbol or address to search for.
    """
    pool_data = search_tokens(token)
    token_data = extract_token_data(token, pool_data)
    return token_data.dict()

# Define supported chains
SUPPORTED_CHAINS = Literal["ethereum", "polygon", "arbitrum", "optimism", "base", "solana", "other"]
class IsTokenReport(BaseModel):
    """Use this tool to record the results of your research into whether the text mentions a token that can be purchased."""
    mentions_purchasable_token: bool = Field(description="Whether the text mentions a token that can be purchased")
    token_symbol: Optional[str] = Field(description="The symbol of the token if mentioned")
    token_chain: Optional[SUPPORTED_CHAINS] = Field(description="The blockchain the token is on if identified") 
    token_address: Optional[str] = Field(description="The token contract address if found")
    is_listed_on_dex: Optional[bool] = Field(description="Whether the token is listed on any DEX")
    trading_pairs: Optional[List[str]] = Field(description="Known trading pairs for this token", default=None)
    confidence_score: int = Field(description="Confidence score from 1-10 on the classification")
    reasoning: str = Field(description="Explanation of why this text is classified as mentioning a purchasable token or not")


# Agent as Tool
class GenerateAlpha(BaseModel):
    """Generate a report analyzing potential token opportunities based on the research. 
Use this when you have sufficient research to report on token opportunities or have reached search limits."""
    token: str = Field(description="The token symbol to analyze")
