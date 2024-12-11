from langchain_core.tools import tool
from typing import List, Dict, Optional, Union, Annotated
from pydantic import BaseModel, Field
import requests

from agents.models import TokenData
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



def extract_token_data(token_symbol: str, pool_data: dict) -> Optional[TokenData]:
    if not pool_data.get('data'):
        return None
        
    pool_name = pool_data['data'][0]['attributes']['name']
    chain = pool_data['data'][0]['relationships']['base_token']['data']['id'].split('_')[0]
    address = pool_data['data'][0]['relationships']['base_token']['data']['id'].split('_')[1]
    attributes = pool_data['data'][0]['attributes']
    
    # Extract symbol from pool name (e.g. "CLANKER / WETH 1%" -> "CLANKER")
    symbol = pool_name.split('/')[0].strip()
    if token_symbol.lower() not in [symbol.lower(), address.lower()]:
        return None
    
    return TokenData(
        chain=chain,
        address=address,
        name='',
        symbol=symbol,
        attributes=attributes
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
    return extract_token_data(token, pool_data)


class IsTokenReport(BaseModel):
    """Use this tool to record the results of your research into whether the text mentions a token that can be purchased."""
    mentions_purchasable_token: bool = Field(description="Whether the text mentions a token that can be purchased")
    token_symbol: Optional[str] = Field(description="The symbol of the token if mentioned")
    token_chain: Optional[str] = Field(description="The blockchain the token is on if identified")
    token_address: Optional[str] = Field(description="The token contract address if found")
    is_listed_on_dex: Optional[bool] = Field(description="Whether the token is listed on any DEX")
    trading_pairs: Optional[List[str]] = Field(description="Known trading pairs for this token", default=None)
    confidence_score: int = Field(description="Confidence score from 1-10 on the classification")
    reasoning: str = Field(description="Explanation of why this text is classified as mentioning a purchasable token or not")


# Agent as Tool
class GenerateReport(BaseModel):
    """Generate a report analyzing potential token opportunities based on the research. 
Use this when you have sufficient research to report on token opportunities or have determined that the messages are not relevant to token opportunities or have reached search limits."""
    messages: List[str] = Field(description="The original Warpcast messages to analyze")