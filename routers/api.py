import random
import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from chains.seek_alpha_chain import base_seek_alpha, multi_hop_seek_alpha
from chains.alpha_chain import Alpha
from agents.multi_agent_alpha_scout import multi_agent_alpha_scout
from agents.models import TokenAlpha, Chain
from agents.tools import IsTokenReport
from database import create_alpha_report, get_all_alpha_reports, TokenOpportunityDB, AlphaReportDB, get_session

load_dotenv()

header_scheme = APIKeyHeader(name="x-key")

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

@router.get("/alpha_reports")
async def get_alpha_reports():
    """Get all alpha reports from the database."""
    try:
        with get_session() as session:
            # Use joinedload to eagerly load the opportunities relationship
            reports = session.query(AlphaReportDB).options(joinedload(AlphaReportDB.opportunities)).all()
            
            # Convert SQLModel objects to dictionaries with proper serialization
            return [
                {
                    "id": report.id,
                    "is_relevant": report.is_relevant,
                    "analysis": report.analysis,
                    "message": report.message,
                    "created_at": report.created_at.isoformat(),
                    "opportunities": [
                        {
                            "name": opp.name,
                            "chain": str(opp.chain),
                            "contract_address": opp.contract_address,
                            "market_cap": float(opp.market_cap) if opp.market_cap else None,
                            "community_score": opp.community_score,
                            "safety_score": opp.safety_score,
                            "justification": opp.justification,
                            "sources": opp.sources,
                            "recommendation": opp.recommendation,
                            "created_at": opp.created_at.isoformat()
                        }
                        for opp in report.opportunities
                    ]
                }
                for report in reports
            ]
    except Exception as e:
        print(f"Error in get_alpha_reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )

@router.post(
    "/base_seek_alpha",
    dependencies=[Depends(api_key_auth)],
    response_model=Alpha
)
async def get_base_seek_alpha(token: Token):
    try:
        alpha = await base_seek_alpha.ainvoke({'token': token})
        return alpha
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/multi_hop_seek_alpha",
    dependencies=[Depends(api_key_auth)],
    response_model=Alpha
)
async def get_multi_hop_seek_alpha(token: Token):
    try:
        alpha = await multi_hop_seek_alpha.ainvoke({'token': token})
        return alpha
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/multi_agent_alpha_scout",
    dependencies=[Depends(api_key_auth)],
    response_model=TokenAlpha
)
async def get_multi_agent_alpha_scout(token_report: IsTokenReport):
    #try:
    # Pass the token report to the alpha scout agent
    token_alpha = await multi_agent_alpha_scout.ainvoke({
        'messages': [token_report.reasoning],
        'token_report': token_report.dict()
    })
    
    # Create report in database
    report_data = {
        "is_relevant": token_report.mentions_purchasable_token,
        "analysis": token_report.reasoning,
        "message": token_report.reasoning,
        "opportunities": [token_alpha]
    }
    
    db_report = create_alpha_report(report_data)
    if not db_report:
        raise HTTPException(
            status_code=500,
            detail="Failed to save report to database"
        )
    
    return token_alpha
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))
