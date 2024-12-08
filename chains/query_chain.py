from langchain_core.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
#from dspy.predict.langchain import LangChainPredict
#import dspy
from operator import itemgetter
from typing import Annotated
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI

#lm = dspy.LM('openai/gpt-4o', max_tokens=5000)
#dspy.configure(lm=lm)

llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True, name='query_llm')


class QueryOutput(BaseModel):
    """Use to generate a question that will help evaluate the token 
and determine if there is alpha to be made.
"""
    query: Annotated[str, ..., "The question that will reveal alpha about the token."]

    def __str__(self):
        return self.query


prompt = ChatPromptTemplate.from_template(
    """
Token:
{token}

Alpha Leaks:
{research}


You are the head of a small crypto trading team at a wall street hedge fund. Your job is to find alpha in the crypto market with 
a special focus on meme coins. You are very good at your job, and you love to find alpha.

Given, the Token and the Alpha Leaks you have so far, write a follow up question that will help determine if there 
is alpha to be made. The follow-up question should be with respect to the Alpha Leaks (if any) and
should include specific information from the Alpha Leaks if needed, because the Alpha Leaks information won't be
available to your teammate that receives this follow up question.
"""
)

tools = [QueryOutput]
get_query = lambda x: x.query

chain = (
    prompt 
    | llm.bind_tools(tools) 
    | PydanticToolsParser(tools=tools, first_tool_only=True)
    | get_query
).with_config({"run_name": "Get Query"})

#dspy_chain = (
#    LangChainPredict(prompt, llm.bind_tools(tools))
#    | PydanticToolsParser(tools=tools, first_tool_only=True)
#)


def get_query(content: str) -> str:
    res = chain.invoke(content)
    return [st.strip() for st in res.split('\n')]