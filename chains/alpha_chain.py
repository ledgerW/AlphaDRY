from langchain_core.output_parsers import StrOutputParser, PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents.base import Document
#import dspy
#from dspy.predict.langchain import LangChainPredict
from typing import Optional, List, Dict, Annotated
from typing_extensions import TypedDict
from enum import Enum
from pydantic import BaseModel, Field, AnyHttpUrl
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI


class ActionEnum(str, Enum):
    buy = 'Buy'
    sell = 'Sell'
    hold = 'Hold'

    def __str__(self):
        return str(self.value)


class AlphaLeaks(TypedDict):
    """Alpha Leaks (reference material) that support the Alpha Action."""
    
    title: Annotated[str, ..., "The title of the reference"]
    leak: Annotated[str, ..., "The source URL of the reference"]
    summary: Annotated[str, ..., "Brief summary of the content in the reference material."]


class Alpha(BaseModel):
    """Use to record your Alpha analysis and action for the given crypto token."""

    action: ActionEnum = Field(description="The action to take that will yield alpha.")
    juice: str = Field(description="Justification for the action . Must be derived from the Alpha Leaks.")
    leaks: List[AlphaLeaks] = Field(description="The Leaks (references) used to actually justify the action.")


llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='alpha_llm')

prompt = ChatPromptTemplate.from_template(
    """
Token:
{token}

    
Leaks:
{research}


You are an expert alpha generator. Your job is to analyze the token and the leaks and provide an action to take that will yield alpha.
The leaks are provided by other members of your team.
"""
)

tools = [Alpha]

chain = (
    prompt
    | llm.bind_tools(tools)
    | PydanticToolsParser(tools=tools, first_tool_only=True, name='alpha')
).with_config({"run_name": "Get Alpha"})

#dspy_chain = (
#    LangChainPredict(prompt, llm.bind_tools(tools))
#    | PydanticToolsParser(tools=tools, first_tool_only=True)
#)


def init_chain(settings: Dict):
    llm = ChatOpenAI(model=settings["Model"], streaming=True)
    chain = (
        prompt
        | llm.bind_tools(tools)
        | PydanticToolsParser(tools=tools, first_tool_only=True)
    )
    
    return chain