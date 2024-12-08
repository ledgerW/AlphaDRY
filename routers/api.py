import random
import os

from fastapi import APIRouter, Depends
from fastapi import Security, HTTPException, status
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
#from auth import check_api_key

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from operator import itemgetter
from typing import Optional, List, Dict, TypedDict, Annotated
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

from chains.seek_alpha_chain import base_seek_alpha, multi_hop_seek_alpha
from chains.alpha_chain import Alpha
from agents.multi_agent_alpha_scout import multi_agent_alpha_scout, AlphaReport


header_scheme = APIKeyHeader(name="x-key")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def api_key_auth(api_key: str = Depends(header_scheme)):
    if api_key != os.environ['API_KEY']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )


class Token(BaseModel):
    name: str
    symbol: str
    chain: str

    def __str__(self):
        return f"Token(name={self.name}, symbol={self.symbol}, chain={self.chain})"



router = APIRouter(prefix="/api", tags=["api"])

@router.post(
    "/base_seek_alpha",
    dependencies=[Depends(api_key_auth)],
    response_model=Alpha
)
async def get_base_seek_alpha(token: Token):
    #try:
    alpha = await base_seek_alpha.ainvoke({'token': token})
    return alpha
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/multi_hop_seek_alpha",
    dependencies=[Depends(api_key_auth)],
    response_model=Alpha
)
async def get_multi_hop_seek_alpha(token: Token):
    #try:
    alpha = await multi_hop_seek_alpha.ainvoke({'token': token})
    return alpha
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/multi_agent_alpha_scout",
    dependencies=[Depends(api_key_auth)],
    response_model=AlphaReport
)
async def get_multi_agent_alpha_scout(messages: List[str]):
    #try:
    alpha = await multi_agent_alpha_scout.ainvoke({'messages': messages})
    return alpha
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))