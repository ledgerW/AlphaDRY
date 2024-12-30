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

from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

from agents.models import TokenAlpha, TokenData, Chain, TransactionData
from agents.tools import quick_search, deep_search, get_token_data, IsTokenReport, GenerateAlpha


# State
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research: Optional[List[ToolMessage]]
    token_report: Optional[IsTokenReport]
    transaction_data: Optional[TransactionData]
    social_media_summary: Optional[str]
    alpha: Optional[TokenAlpha]
    review_feedback: Optional[str]
    next: str
    quick_search_count: int
    deep_search_count: int
    get_token_data_count: int
    improved: int


# Research Agent
def research_agent(state: GraphState) -> GraphState:
    """Agent that performs research on the token opportunity"""

    def next_action(message: AIMessage, state: GraphState) -> tuple[str, list[str]]:
        if not message.tool_calls:
            return 'research', []
            
        tool_names = []
        for tool_call in message.tool_calls:
            tool_name = tool_call['name']
            tool_names.append(tool_name)
            
        # Check search limits after collecting all tool names
        for tool_name in tool_names:
            if (tool_name == 'quick_search' and state['quick_search_count'] >= 3) or \
                (tool_name == 'deep_search' and state['deep_search_count'] >= 3) or \
                (tool_name == 'get_token_data' and state['get_token_data_count'] >= 2):
                return 'GenerateAlpha', tool_names
        
        # If we get here, either no search tools were used or none hit their limits
        if any(name in ['quick_search', 'deep_search', 'get_token_data'] for name in tool_names):
            return 'research', tool_names
            
        # For any other tool calls
        return tool_names[0], tool_names

    tools = [quick_search, deep_search, get_token_data, GenerateAlpha]

    # Calculate remaining searches
    quick_search_remaining = 3 - state['quick_search_count']
    deep_search_remaining = 3 - state['deep_search_count']
    get_token_data_remaining = 2 - state['get_token_data_count']

    # Get research messages
    research = [msg for msg in state['messages'] if isinstance(msg, ToolMessage)]
    token_report = state.get('token_report', None)

    # Find get_token_data message and extract transaction data
    transaction_data = None
    for msg in reversed(research):
        if msg.name == 'get_token_data' and msg.content:
            #try:
            # Convert string content to dict if needed
            transaction_data = msg.content
            break

    if 'review_feedback' not in state:
        state['review_feedback'] = None
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an expert crypto researcher focused on analyzing token opportunities.
Your goal is to research the provided token and determine if it represents a good investment opportunity.

Focus your research on:
1. Market cap and trading data
2. Community activity and team reputation
3. Contract safety and audits
4. Recent developments and announcements

Token Information:
Symbol: {token_report['token_symbol'] if token_report else 'Unknown'}
Chain: {token_report['token_chain'] if token_report else 'Unknown'}
Address: {token_report['token_address'] if token_report else 'Unknown'}

Social Media Activity:
{state.get('social_media_summary', 'No social media data available.')}

IMPORTANT: You have limited tool usage available:
- Quick Search: {quick_search_remaining} remaining
- Deep Search: {deep_search_remaining} remaining
- Get Token Data: {get_token_data_remaining} remaining

Available tools:
- quick_search: Use for initial research on token mentions, news, and basic information
- deep_search: Use for detailed research on specific aspects like team, contracts, or developments
- get_token_data: Use to fetch market data, trading info and DEX details for a specific token
- GenerateAlpha: Use when you have sufficient research or have reached search limits to create the final analysis

Review feedback:
{state['review_feedback']}

You must conduct follow-up research to address comments in the review feedback.

You must use one of your available tools."""),
        MessagesPlaceholder(variable_name="messages")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='researcher_llm')\
        .bind_tools(tools, tool_choice='required')
    
    chain = prompt | llm
    
    message = chain.invoke({
        "messages": state["messages"]
    })

    next, tool_names = next_action(message, state)
    
    # Update search counters
    new_quick_count = state['quick_search_count']
    new_deep_count = state['deep_search_count']
    new_get_token_data_count = state['get_token_data_count']
    
    if 'quick_search' in tool_names:
        new_quick_count += 1
    if 'deep_search' in tool_names:
        new_deep_count += 1 
    if 'get_token_data' in tool_names:
        new_get_token_data_count += 1
    
    return {
        'messages': [message], 
        'research': research,
        'token_report': token_report,
        'transaction_data': transaction_data,
        'next': next,
        'quick_search_count': new_quick_count,
        'deep_search_count': new_deep_count,
        'get_token_data_count': new_get_token_data_count
    }


# Alpha Writer Agent
def generate_alpha(state: GraphState) -> GraphState:
    """Generate the final token opportunity analysis based on all research gathered"""
    
    research = state['research']
    token_report = state['token_report']
    transaction_data = state['transaction_data']
    social_media_summary = state.get('social_media_summary', 'No social media data available.')
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an expert crypto analyst specializing in early-stage tokens.
Your task is to analyze the research and determine if this token represents a good investment opportunity.

Key criteria:
- Market cap below $5M
- Active and reputable community
- Trading momentum (are we early or late in the cycle?)
- Safe and audited contracts
- Early stage with growth potential

Consider both on-chain data and social media activity when evaluating community engagement and momentum.

Only recommend tokens that meet these criteria and have strong supporting evidence."""),
        HumanMessage(content=f"""Token Report:
{token_report}


Social Media Summary:
{social_media_summary}


Research:
{research}


Transaction Data:
{transaction_data}


Generate a detailed token opportunity analysis. Focus on safety and evidence-based analysis.""")
    ])

    tools = [TokenAlpha]
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='alpha_writer_llm')\
        .bind_tools(tools, tool_choice='required')
    
    chain = prompt | llm

    result = chain.invoke({})
    
    # Extract the tool call arguments and ensure they match TokenAlpha model
    if not result.tool_calls or not result.tool_calls[0]['args']:
        raise ValueError("No alpha analysis generated")
        
    alpha_data = result.tool_calls[0]['args']
    
    # Create TokenAlpha instance to validate the data
    token_alpha = TokenAlpha(**alpha_data)
    return {'alpha': token_alpha.dict()}


# Add this near the top with other models
class ReviewFeedback(BaseModel):
    """Feedback from the review of a token opportunity analysis"""
    next: Annotated[
        Literal["research", "FINISH"],
        "Does this analysis need more research, or is it FINISHED?"
    ]
    comments: Annotated[
        str,
        "If recommending more research, explain what needs to be investigated. If finished, summarize why the analysis is complete."
    ]

def reviewer(state: GraphState) -> GraphState:
    """Agent that reviews the generated opportunity analysis for completeness and accuracy"""
    
    tools = [ReviewFeedback]
    
    # Calculate remaining searches for context
    quick_search_remaining = 3 - state['quick_search_count']
    deep_search_remaining = 3 - state['deep_search_count']
    get_token_data_remaining = 2 - state['get_token_data_count']
    social_media_summary = state.get('social_media_summary', 'No social media data available.')
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an expert crypto research reviewer focused on ensuring thorough analysis of token opportunities.
Your goal is to review the generated Token Alpha analysis to ensure:

1. All claims are supported by research
2. Important information isn't missing
3. The logic and conclusions are sound
4. Risk factors are properly considered


A high quality analysis will:
a) Have complete information about the token opportunity
b) Include evidence to support all claims
c) Consider potential risks and red flags
d) Make a clear recommendation based on evidence

Token Report:
{state['token_report']}


Social Media Summary:
{social_media_summary}


Token Alpha:
{state['alpha']}


Review the Alpha above. Consider:
1. Is all important information included and verified?
2. Are the conclusions supported by evidence?
3. Have risks been properly assessed?
4. Is the recommendation justified?

Provide your review feedback using the ReviewFeedback tool.""")])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='reviewer_llm')\
        .bind_tools(tools, tool_choice='required')
    
    chain = prompt | llm
    
    message = chain.invoke({})
  
    review_message = ToolMessage(
        content=message.tool_calls[0]['args']['comments'],
        tool_call_id=state['messages'][-1].tool_calls[0]['id'],
        name='review',
        status='success'
    )
    
    try:
        next = 'FINISH' if state['improved'] >= 1 else message.tool_calls[0]['args']['next']
    except:
        next = message.tool_calls[0]['args']['next']
    
    return {
        'messages': state['messages'] + [review_message],
        'research': state.get('research', []),
        'token_report': state['token_report'],
        'alpha': state['alpha'],
        'review_feedback': review_message.content,
        'improved': state['improved'] + 1,
        'next': next,
        'quick_search_count': state['quick_search_count'],
        'deep_search_count': state['deep_search_count'],
        'get_token_data_count': state['get_token_data_count']
    }


# Tool Nodes
research_tools_node = ToolNode([quick_search, deep_search, get_token_data])

# The Graph
graph = StateGraph(GraphState)

graph.add_node('researcher', research_agent)
graph.add_node('research_tools', research_tools_node)
graph.add_node('alpha_writer', generate_alpha)
graph.add_node('reviewer', reviewer)
graph.add_edge(START, 'researcher')
graph.add_conditional_edges(
    'researcher', lambda x: x['next'], {
        'research': 'research_tools',
        'GenerateAlpha': 'alpha_writer',
    })
graph.add_edge('research_tools', 'researcher')
graph.add_edge('alpha_writer', 'reviewer')
graph.add_conditional_edges(
    'reviewer', lambda x: x['next'], {
        'research': 'researcher',
        'FINISH': END
    })

agent_graph = graph.compile()
agent_graph.name = "Multi-Agent Alpha Scout"


# As Chain
def get_state(input_data):
    messages = [HumanMessage(content=msg) for msg in input_data.get('messages', [])]
    token_report = input_data.get('token_report')
    social_media_summary = input_data.get('social_media_summary')
    
    return GraphState(
        messages=messages,
        research=None,
        token_report=token_report,
        social_media_summary=social_media_summary,
        alpha=None,
        review_feedback=None,
        next='',
        quick_search_count=0,
        deep_search_count=0,
        get_token_data_count=0,
        improved=0
    )

get_alpha = lambda x: x['alpha']

multi_agent_alpha_scout = (
    RunnablePassthrough.assign(token_report=lambda x: x.get('token_report'))
    | get_state 
    | agent_graph
    | get_alpha
).with_config({"run_name": "Multi-Agent Alpha Scout"})
