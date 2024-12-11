from typing import List, Optional, Sequence, Annotated
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

from pydantic import BaseModel, Field

from agents.tools import quick_search, get_token_data, IsTokenReport



# State
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research: Optional[List[ToolMessage]]
    report: Optional[IsTokenReport]
    next: str
    quick_search_count: int
    get_token_data_count: int


# Research Agent
def research_agent(state: GraphState) -> GraphState:
    """Agent that analyzes text to determine if it mentions a purchasable token"""

    def next_action(message: AIMessage, state: GraphState) -> tuple[str, list[str]]:
        if not message.tool_calls:
            return 'research', []
            
        tool_names = []
        for tool_call in message.tool_calls:
            tool_name = tool_call['name']
            tool_names.append(tool_name)
            
        # Check search limits
        if ((tool_name == 'quick_search' and state['quick_search_count'] >= 2) or
            (tool_name == 'get_token_data' and state['get_token_data_count'] >= 2)):
            return 'researcher', tool_names
        
        if any(name in ['quick_search', 'get_token_data'] for name in tool_names):
            return 'research', tool_names

        if 'IsTokenReport' in tool_names:
            return 'FINISH', tool_names
            
        return tool_names[0], tool_names

    tools = [quick_search, get_token_data, IsTokenReport]

    # Calculate remaining searches
    quick_search_remaining = 2 - state['quick_search_count']
    get_token_data_remaining = 2 - state['get_token_data_count']
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an expert crypto analyst focused on identifying mentions of purchasable cryptocurrency tokens in text.
Your goal is to determine if the input text is discussing a token that can actually be purchased on exchanges or DEXes.

Focus on identifying:
1. Token symbols (usually in ALL CAPS)
2. Contract addresses (long hexadecimal strings)
3. Blockchain mentions (e.g. Base, Solana, etc.)
4. Trading pairs or exchange listings
5. Purchase-related terminology (buy, trade, swap, etc.)

Ignore:
- General crypto discussion without specific tokens
- Theoretical or upcoming tokens not yet available
- Scam or suspicious token mentions

IMPORTANT: Limit your tool usage to 2 calls per tool, but don't hesitate to use all your tool calls.
- Quick Search: {quick_search_remaining} remaining
- Get Token Data: {get_token_data_remaining} remaining

When you have enough information or have reached search limits, use the IsTokenReport tool to submit your final classification.

Initial message:
{state['messages'][0]}
"""),
        MessagesPlaceholder(variable_name="messages"),
        SystemMessage(content="""Based on the work done so far and your remaining tool usage limits, what's your next action?
- Use quick_search to verify token existence and find trading information
- Use get_token_data to confirm token contract and trading status
- Use IsTokenReport to submit your final classification if:
    1. You've confirmed whether the token is purchasable
    2. You have reached search limits
    3. You've determined there's no purchasable token mentioned

You must use one of your available tools.""")
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True)\
        .bind_tools(tools, tool_choice='required')
    
    chain = prompt | llm
    
    message = chain.invoke({
        "messages": state["messages"]
    })
    
    next, tool_names = next_action(message, state)
    
    # Update search counters
    new_quick_count = state['quick_search_count']
    new_get_token_data_count = state['get_token_data_count']
    
    if 'quick_search' in tool_names:
        new_quick_count += 1
    if 'get_token_data' in tool_names:
        new_get_token_data_count += 1
    
    report = None
    if message.tool_calls and message.tool_calls[0]['name'] == 'IsTokenReport':
        report = message.tool_calls[0]['args']
    
    return {
        'messages': [message],
        'research': state.get('research', []),
        'report': report,
        'next': next,
        'quick_search_count': new_quick_count,
        'get_token_data_count': new_get_token_data_count
    }


# Tool Node
research_tools_node = ToolNode([quick_search, get_token_data])

# The Graph
graph = StateGraph(GraphState)

graph.add_node('researcher', research_agent)
graph.add_node('research_tools', research_tools_node)

graph.add_edge(START, 'researcher')
graph.add_conditional_edges(
    'researcher', lambda x: x['next'], {
        'research': 'research_tools',
        'researcher': 'researcher',
        'FINISH': END
    })
graph.add_edge('research_tools', 'researcher')

agent_graph = graph.compile()
agent_graph.name = "Token Finder"


# As Chain
get_state = lambda x: GraphState(
    messages=x['messages'],
    research=None,
    report=None,
    next='',
    quick_search_count=0,
    get_token_data_count=0
)
get_report = lambda x: x['report']
get_messages = lambda x: [HumanMessage(content=msg) for msg in x['messages']]

crypto_text_classifier = (
    RunnablePassthrough.assign(messages=get_messages)
    | get_state 
    | agent_graph
    | get_report
).with_config({"run_name": "Token Finder"})
