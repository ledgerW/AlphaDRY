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

from agents.models import AlphaReport
from agents.tools import quick_search, deep_search, GenerateReport, get_token_data



# State
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research: Optional[List[ToolMessage]]
    report: Optional[AlphaReport]
    review_feedback: Optional[str]
    next: str
    quick_search_count: int
    deep_search_count: int
    get_token_data_count: int
    improved: int


# Research Agent
def research_agent(state: GraphState) -> GraphState:
    """Agent that performs research on potential token opportunities"""

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
                return 'GenerateReport', tool_names
        
        # If we get here, either no search tools were used or none hit their limits
        if any(name in ['quick_search', 'deep_search', 'get_token_data'] for name in tool_names):
            return 'research', tool_names
            
        # For any other tool calls
        return tool_names[0], tool_names

    tools = [quick_search, deep_search, get_token_data, GenerateReport]

    # Calculate remaining searches
    quick_search_remaining = 3 - state['quick_search_count']
    deep_search_remaining = 3 - state['deep_search_count']
    get_token_data_remaining = 3 - state['get_token_data_count']

    if 'review_feedback' not in state:
        state['review_feedback'] = None
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an expert crypto researcher focused on identifying promising early-stage tokens.
Your goal is to gather comprehensive information about potential opportunities mentioned in messages.
First, determine if the messages are relevant to token opportunities, and if so, gather information about the token, including 
token data from the get_token_data tool.

It's very important to get the structured token data from the get_token_data tool, if it's available.

Focus your research on:
1. Token contracts and audits
2. Market cap and trading data
3. Community activity and team reputation
4. Recent developments and announcements

IMPORTANT: You have limited tool usage available:
- Quick Search: {quick_search_remaining} remaining
- Deep Search: {deep_search_remaining} remaining
- Get Token Data: {get_token_data_remaining} remaining

When you reach the search limits, you must generate your report with the information gathered.
You must also use the Get Token Data tool at least once."""),
        MessagesPlaceholder(variable_name="messages"),
        SystemMessage(content=f"""Based on the work done so far and your remaining tool usage limits, what's your next action?
- Use quick_search to gather basic information (if searches remain)
- Use deep_search to gather detailed information (if searches remain)
- Use get_token_data to gather token data (if tool usage remains)
- Use GenerateReport IF and ONLY IF:
    - you have addressed all review feedback with follow-up research
    - you have all the information you need
    - you have reached search limits
    - you have determined that the messages are not relevant to token opportunities

Review feedback:
{state['review_feedback']}

You must use one of your available tools.""")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='researcher_llm')\
        .bind_tools(tools, tool_choice='required')
    
    chain = prompt | llm
    
    message = chain.invoke({
        "messages": state["messages"]
    })
    
    research = [msg for msg in state['messages'] if isinstance(msg, ToolMessage)]
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
        'next': next,
        'quick_search_count': new_quick_count,
        'deep_search_count': new_deep_count,
        'get_token_data_count': new_get_token_data_count
    }


# Report Writer Agent
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
    return {'report': result.tool_calls[0]['args']}


# Add this near the top with other models
class ReviewFeedback(BaseModel):
    """Feedback from the review of an alpha report"""
    next: Annotated[
        Literal["research", "FINISH"],
        "Does this Report need more research, or is it FINISHED?"
    ]
    comments: Annotated[
        str,
        "If recommending more research, explain what needs to be investigated. If finished, summarize why the report is complete."
    ]

def reviewer(state: GraphState) -> GraphState:
    """Agent that reviews the generated report for completeness and accuracy"""
    
    tools = [ReviewFeedback]
    
    # Calculate remaining searches for context
    quick_search_remaining = 3 - state['quick_search_count']
    deep_search_remaining = 3 - state['deep_search_count']
    get_token_data_remaining = 2 - state['get_token_data_count']
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an expert crypto research reviewer focused on ensuring thorough analysis of token opportunities.
Your goal is to review the generated report and original messages to ensure:

1. No potential opportunities were missed (especially check for ALL CAPS text that might be token symbols)
2. All claims in the report are supported by research
3. Important information isn't missing
4. The logic and conclusions are sound
5. If marked as "not relevant", verify this is correct

Available tool usage remaining:
- Quick Search: {quick_search_remaining}
- Deep Search: {deep_search_remaining}
- Get Token Data: {get_token_data_remaining}

A high quality report will:
a) Have complete information about the token opportunity
b) Include evidence to support all claims
c) Consider potential risks and red flags
d) Not dismiss opportunities without thorough investigation

Review the report carefully and decide if more research is needed or if it's ready to finalize.

Original Messages:
{state['messages'][0]}

Report:
{state['report']}


Review the report and research above. Consider:
1. Any words in all CAPS in the original message must be quick searched at least once!
2. If marked as "not relevant", are you sure? Crypto discussions often use unusual slang
3. Is all important information included and verified?
4. Are the conclusions supported by evidence?

Provide your review feedback using the ReviewFeedback tool.""")])

    llm = ChatOpenAI(model="gpt-4", temperature=0.1, streaming=True, name='reviewer_llm')\
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
        next = 'FINISH' if state['improved'] >= 2 else message.tool_calls[0]['args']['next']
    except:
        next = message.tool_calls[0]['args']['next']
    
    return {
        'messages': state['messages'] + [review_message],
        'research': state.get('research', []),
        'report': state['report'],
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
graph.add_node('report_writer', generate_report)
graph.add_node('reviewer', reviewer)
graph.add_edge(START, 'researcher')
graph.add_conditional_edges(
    'researcher', lambda x: x['next'], {
        'research': 'research_tools',
        'GenerateReport': 'report_writer',
    })
graph.add_edge('research_tools', 'researcher')
graph.add_edge('report_writer', 'reviewer')
graph.add_conditional_edges(
    'reviewer', lambda x: x['next'], {
        'research': 'researcher',
        'FINISH': END
    })

agent_graph = graph.compile()
agent_graph.name = "Multi-Agent Alpha Scout"


# As Chain
get_state = lambda x: GraphState(
    messages=x['messages'],
    research=None,
    improved=False,
    report=None,
    review_feedback=None,
    next='',
    quick_search_count=0,
    deep_search_count=0,
    get_token_data_count=0
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
