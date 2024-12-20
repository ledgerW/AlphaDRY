import random
import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from chains.seek_alpha_chain import base_seek_alpha, multi_hop_seek_alpha
from chains.alpha_chain import Alpha
from agents.multi_agent_alpha_scout import multi_agent_alpha_scout
from agents.multi_agent_token_finder import crypto_text_classifier
from agents.models import TokenAlpha, Chain
from agents.tools import IsTokenReport
from database import (
    create_alpha_report, get_all_alpha_reports, TokenOpportunityDB, 
    AlphaReportDB, get_session, create_social_media_post,
    create_token_report
)

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

class SocialMediaInput(BaseModel):
    """Input model for social media text analysis"""
    text: str = Field(..., description="The social media post text to analyze")
    source: str = Field(default="unknown", description="Source platform of the post")
    author_id: str = Field(default="unknown", description="Author's ID in the source platform")
    author_username: str = Field(default="unknown", description="Author's username")
    author_display_name: str = Field(default=None, description="Author's display name")
    post_id: str = Field(default=None, description="Original post ID from the source")
    original_timestamp: datetime = Field(default=None, description="Original post date/time from the source platform")

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

@router.post(
    "/analyze_social_post",
    dependencies=[Depends(api_key_auth)],
    response_model=IsTokenReport
)
async def analyze_social_post(input_data: SocialMediaInput):
    """Analyze social media post text for token mentions and create a token report."""
    try:
        # Convert input data to dict and handle datetime serialization
        raw_data = input_data.dict()
        if raw_data.get('original_timestamp'):
            raw_data['original_timestamp'] = raw_data['original_timestamp'].isoformat()

        # Create social media post entry
        post_data = {
            "source": input_data.source,
            "post_id": input_data.post_id or f"generated_{int(datetime.utcnow().timestamp())}",
            "author_id": input_data.author_id,
            "author_username": input_data.author_username,
            "author_display_name": input_data.author_display_name,
            "text": input_data.text,
            "original_timestamp": input_data.original_timestamp or datetime.utcnow(),  # Use current time if not provided
            "timestamp": datetime.utcnow(),  # When we process the post
            "reactions_count": 0,
            "replies_count": 0,
            "reposts_count": 0,
            "raw_data": raw_data  # Use the serialized version
        }
        
        social_post = create_social_media_post(post_data)
        if not social_post:
            raise HTTPException(
                status_code=500,
                detail="Failed to save social media post to database"
            )

        # Analyze text using token finder agent
        token_report = await crypto_text_classifier.ainvoke({
            'messages': [input_data.text]
        })

        if not token_report:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze text with token finder agent"
            )

        # Save token report to database and get the saved object
        db_token_report = create_token_report(token_report, social_post.id)
        if not db_token_report:
            raise HTTPException(
                status_code=500,
                detail="Failed to save token report to database"
            )

        # Merge the database ID with the token report data
        token_report_with_id = {**token_report, "id": db_token_report.id}
        return token_report_with_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/analyze_and_scout",
    dependencies=[Depends(api_key_auth)],
    response_model=TokenAlpha | None
)
async def analyze_and_scout(input_data: SocialMediaInput):
    """Analyze social media post and scout for token opportunities in one step."""
    try:
        # First analyze the social post
        token_report = await analyze_social_post(input_data)
        
        # Only run alpha scout if a purchasable token was found
        if token_report['mentions_purchasable_token']:
            # Create IsTokenReport instance for the multi_agent_alpha_scout endpoint
            token_report_model = IsTokenReport(**token_report)
            
            # Call the multi_agent_alpha_scout endpoint
            token_alpha = await get_multi_agent_alpha_scout(token_report_model)
            
            # Update the alpha report with token_report_id
            report_data = {
                "is_relevant": token_report['mentions_purchasable_token'],
                "analysis": token_report['reasoning'],
                "message": token_report['reasoning'],
                "opportunities": [token_alpha],
                "token_report_id": token_report['id']
            }
            
            db_report = create_alpha_report(report_data)
            if not db_report:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save report to database"
                )
            
            return token_alpha
        
        # If no purchasable token found, return None
        return None
        
    except Exception as e:
        print(f"Error in analyze_and_scout: {str(e)}")  # Add error logging
        raise HTTPException(status_code=500, detail=str(e))
