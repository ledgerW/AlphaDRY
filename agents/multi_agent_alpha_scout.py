from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

from typing import Literal, Annotated, List, Sequence, Optional
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.output_parsers import PydanticToolsParser
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.documents.base import Document
from operator import itemgetter

from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.pregel import RetryPolicy

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum
from datetime import datetime

from chains.tavily_chain import retriever as long_retriever, short_retriever


# Models
class Chain(str, Enum):
    BASE = 'Base'
    SOLANA = 'Solana'


class TokenOpportunity(BaseModel):
    """Details about a potential token investment opportunity"""
    name: str = Field(description="Name of the token")
    chain: Chain = Field(description="The blockchain the token is on (Base or Solana)")
    contract_address: Optional[str] = Field(description="Contract address of the token if available")
    market_cap: Optional[float] = Field(description="Current market cap in USD if available")
    community_score: int = Field(description="Score from 1-10 rating the strength and reputation of the community")
    safety_score: int = Field(description="Score from 1-10 rating the safety of the contract and team")
    justification: str = Field(description="Detailed explanation of why this token is a good opportunity")
    sources: List[str] = Field(description="URLs or references supporting the analysis")


class AlphaReport(BaseModel):
    """Final report of token opportunities"""
    is_relevant: bool = Field(description="Whether the input messages are relevant to token opportunities")
    opportunities: List[TokenOpportunity] = Field(description="List of identified token opportunities")
    analysis: str = Field(description="Overall analysis and summary of the opportunities")


# State
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research: Optional[List[ToolMessage]]
    improved: bool
    report: Optional[AlphaReport]
    next: str
    quick_search_count: int
    deep_search_count: int


# Tools
@tool("quick_search")
def quick_search(query: str) -> List[dict]:
    """Do a quick initial web search for basic information about tokens, teams, contracts, and market data."""
    docs = short_retriever.invoke(query)
    return [doc.dict() for doc in docs]

quick_search_node = ToolNode([quick_search])


@tool("deep_search") 
def deep_search(query: str) -> List[dict]:
    """Do a detailed web search to gather comprehensive information about tokens, teams, contracts, and market data."""
    docs = long_retriever.invoke(query)
    return [doc.dict() for doc in docs]


deep_search_node = ToolNode([deep_search])


class GenerateReport(BaseModel):
    """Generate a report analyzing potential token opportunities based on the research"""
    messages: List[str] = Field(description="The original Warpcast messages to analyze")


def generate_report(state: GraphState) -> GraphState:
    """Generate the final alpha report based on all research gathered"""
    
    messages = [msg.content for msg in state['messages'] if isinstance(msg, HumanMessage)]
    research = state['research']

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an expert crypto analyst specializing in early-stage tokens and memecoins.
Your task is to analyze messages and research to identify promising token opportunities, focusing only on Base and Solana chains.

Key criteria:
- Market cap below $5M
- Active and reputable community
- Safe and audited contracts
- Early stage with growth potential

Only include opportunities that meet these criteria and have strong supporting evidence."""),
        HumanMessage(content=f"""Messages to analyze:
        {messages}

Available research:
{research}

Generate a detailed report identifying any promising token opportunities. Focus on safety and evidence-based analysis.""")
    ])

    tools = [AlphaReport]
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='alpha_report_llm').bind_tools(tools)
    chain = prompt | llm

    result = chain.invoke({'messages': messages, 'research': research})
    return {'report': result.tool_calls[0]['args'], 'next': 'FINISH'}


def research_agent(state: GraphState) -> GraphState:
    """Agent that performs research on potential token opportunities"""

    def next_action(message: AIMessage, state: GraphState) -> str:
        if not message.tool_calls:
            return 'research'
            
        tool_name = message.tool_calls[0]['name']
        
        # Check search limits
        if tool_name == 'quick_search' and state['quick_search_count'] >= 3:
            return 'GenerateReport'
        if tool_name == 'deep_search' and state['deep_search_count'] >= 3:
            return 'GenerateReport'
            
        return tool_name

    tools = [quick_search, deep_search, GenerateReport]

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an expert crypto researcher focused on identifying promising early-stage tokens.
Your goal is to gather comprehensive information about potential opportunities mentioned in messages.

Focus your research on:
1. Token contracts and audits
2. Market cap and trading data
3. Community activity and team reputation
4. Recent developments and announcements

IMPORTANT: You have limited searches available:
- Quick Search: {quick_search_remaining}/3 remaining
- Deep Search: {deep_search_remaining}/3 remaining

When you reach the search limits, you must generate your report with the information gathered."""),
        MessagesPlaceholder(variable_name="messages"),
        SystemMessage(content="""Based on the work done so far and your remaining search limits, what's your next action?
- Use quick_search to gather basic information (if searches remain)
- Use deep_search to gather detailed information (if searches remain)
- Use GenerateReport when you have sufficient research or have reached search limits

You must use one of your available tools.""")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='researcher_llm').bind_tools(tools)
    chain = prompt | llm
    
    # Calculate remaining searches
    quick_search_remaining = 3 - state['quick_search_count']
    deep_search_remaining = 3 - state['deep_search_count']
    
    message = chain.invoke({
        "messages": state["messages"],
        "quick_search_remaining": quick_search_remaining,
        "deep_search_remaining": deep_search_remaining
    })
    
    research = [msg for msg in state['messages'] if isinstance(msg, ToolMessage)]
    next = next_action(message, state)
    
    # Update search counters
    new_quick_count = state['quick_search_count']
    new_deep_count = state['deep_search_count']
    
    if next == 'quick_search':
        new_quick_count += 1
    elif next == 'deep_search':
        new_deep_count += 1
    
    return {
        'messages': [message], 
        'research': research, 
        'next': next,
        'quick_search_count': new_quick_count,
        'deep_search_count': new_deep_count
    }


# The Graph
graph = StateGraph(GraphState)

graph.add_node('researcher', research_agent)
graph.add_node('quick_search', quick_search_node)
graph.add_node('deep_search', deep_search_node)
graph.add_node('report_writer', generate_report)

graph.add_edge(START, 'researcher')
graph.add_conditional_edges(
    'researcher', lambda x: x['next'], {
        'quick_search': 'quick_search',
        'deep_search': 'deep_search',
        'GenerateReport': 'report_writer',
    })
graph.add_edge('quick_search', 'researcher')
graph.add_edge('deep_search', 'researcher')
graph.add_edge('report_writer', END)

agent_graph = graph.compile()
agent_graph.name = "Multi-Agent Alpha Scout"

# As Chain
get_state = lambda x: GraphState(
    messages=x['messages'],
    research=None,
    improved=False,
    report=None,
    next='',
    quick_search_count=0,
    deep_search_count=0
)
get_report = lambda x: x['report']
get_messages = lambda x: [HumanMessage(content=msg) for msg in x['messages']]
get_improved = lambda x: False

multi_agent_alpha_scout = (
    RunnablePassthrough.assign(messages=get_messages)
    | get_state 
    | agent_graph
    | get_report
).with_config({"run_name": "Multi-Agent Alpha Scout"})
