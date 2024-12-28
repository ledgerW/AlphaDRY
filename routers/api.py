import random
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

class TokenData(BaseModel):
    symbol: str
    name: str
    chain: str
    address: Optional[str] = None

class TokenOpportunity(BaseModel):
    name: str
    chain: str
    contract_address: Optional[str] = None
    market_cap: Optional[float] = None
    community_score: Optional[int] = None
    safety_score: Optional[int] = None
    justification: str
    sources: List[str]
    recommendation: str
    created_at: datetime
    token: Optional[TokenData] = None
    token_report: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AlphaReport(BaseModel):
    id: int
    is_relevant: bool
    analysis: str
    message: str
    created_at: datetime
    opportunities: List[TokenOpportunity]

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

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
    AlphaReportDB, TokenReportDB, SocialMediaPostDB, TokenDB, get_session, 
    create_social_media_post, create_token_report
)
from sqlalchemy import desc


from db.operations.alpha import has_recent_token_report

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

from datetime import datetime, timedelta
from typing import Optional

@router.get("/alpha_reports")
async def get_alpha_reports(date: Optional[str] = None):
    """Get all alpha reports from the database."""
    try:
        with get_session() as session:
            # Use joinedload to eagerly load the opportunities and their related token_reports and social_media_posts
            query = session.query(AlphaReportDB).options(
                joinedload(AlphaReportDB.opportunities)
                .joinedload(TokenOpportunityDB.token),
                joinedload(AlphaReportDB.opportunities)
                .joinedload(TokenOpportunityDB.token_report)
                .joinedload(TokenReportDB.social_media_post)
                .load_only(
                    SocialMediaPostDB.source,
                    SocialMediaPostDB.author_display_name,
                    SocialMediaPostDB.text,
                    SocialMediaPostDB.timestamp
                )
            )
            
            if date:
                # Convert date string to datetime
                target_date = datetime.strptime(date, '%Y-%m-%d')
                next_date = target_date + timedelta(days=1)
                
                # Filter reports for the specified date
                query = query.filter(
                    AlphaReportDB.created_at >= target_date,
                    AlphaReportDB.created_at < next_date
                )
            
            reports = query.all()
            
            # Convert SQLModel objects to Pydantic models
            reports_data = [
                AlphaReport(
                    id=report.id,
                    is_relevant=report.is_relevant,
                    analysis=report.analysis,
                    message=report.message,
                    created_at=report.created_at,
                    opportunities=[
                        TokenOpportunity(
                            name=opp.name,
                            chain=str(opp.chain),
                            contract_address=opp.contract_address,
                            market_cap=float(opp.market_cap) if opp.market_cap else None,
                            community_score=opp.community_score,
                            safety_score=opp.safety_score,
                            justification=opp.justification,
                            sources=opp.sources,
                            recommendation=opp.recommendation,
                            created_at=opp.created_at,
                            token=TokenData(
                                symbol=opp.token.symbol,
                                name=opp.token.name,
                                chain=str(opp.token.chain),
                                address=opp.token.address
                            ) if opp.token else None,
                            token_report={
                                "social_media_post": {
                                    "source": opp.token_report.social_media_post.source if opp.token_report and opp.token_report.social_media_post else None,
                                    "author_display_name": opp.token_report.social_media_post.author_display_name if opp.token_report and opp.token_report.social_media_post else None,
                                    "text": opp.token_report.social_media_post.text if opp.token_report and opp.token_report.social_media_post else None,
                                    "timestamp": opp.token_report.social_media_post.timestamp if opp.token_report and opp.token_report.social_media_post else None
                                } if opp.token_report and opp.token_report.social_media_post else None
                            } if opp.token_report else None
                        )
                        for opp in report.opportunities
                    ]
                )
                for report in reports
            ]
            from fastapi.encoders import jsonable_encoder
            from fastapi.responses import JSONResponse
            
            # Convert Pydantic models to JSON with proper formatting
            json_data = jsonable_encoder(
                [report.dict(by_alias=True) for report in reports_data],
                exclude_none=True,
                custom_encoder={
                    datetime: lambda dt: dt.isoformat()
                }
            )
            
            # Return a properly formatted JSON response
            return JSONResponse(
                content=json_data,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
    except Exception as e:
        print(f"Error in get_alpha_reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )


@router.get("/token/{address}")
async def get_token(address: str):
    """Get detailed information about a specific token including all relationships."""
    try:
        with get_session() as session:
            token = session.query(TokenDB)\
                .filter(TokenDB.address == address)\
                .options(
                    joinedload(TokenDB.token_reports).joinedload(TokenReportDB.social_media_post),
                    joinedload(TokenDB.token_opportunities)
                )\
                .first()
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Token not found"
                )
            
            return {
                "id": token.id,
                "symbol": token.symbol,
                "name": token.name,
                "chain": str(token.chain),
                "address": token.address,
                "created_at": token.created_at.isoformat(),
                "token_reports": [
                    {
                        "id": report.id,
                        "mentions_purchasable_token": report.mentions_purchasable_token,
                        "token_symbol": report.token_symbol,
                        "token_chain": report.token_chain,
                        "token_address": report.token_address,
                        "is_listed_on_dex": report.is_listed_on_dex,
                        "trading_pairs": report.trading_pairs,
                        "confidence_score": report.confidence_score,
                        "reasoning": report.reasoning,
                        "created_at": report.created_at.isoformat(),
                        "social_media_post": {
                            "id": report.social_media_post.id,
                            "source": report.social_media_post.source,
                            "post_id": report.social_media_post.post_id,
                            "author_id": report.social_media_post.author_id,
                            "author_username": report.social_media_post.author_username,
                            "author_display_name": report.social_media_post.author_display_name,
                            "text": report.social_media_post.text,
                            "original_timestamp": report.social_media_post.original_timestamp.isoformat(),
                            "timestamp": report.social_media_post.timestamp.isoformat(),
                            "reactions_count": report.social_media_post.reactions_count,
                            "replies_count": report.social_media_post.replies_count,
                            "reposts_count": report.social_media_post.reposts_count,
                            "created_at": report.social_media_post.created_at.isoformat()
                        } if report.social_media_post else None
                    }
                    for report in token.token_reports
                ],
                "token_opportunities": [
                    {
                        "id": opp.id,
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
                    for opp in token.token_opportunities
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch token: {str(e)}"
        )

@router.get("/tokens")
async def get_tokens():
    """Get all tokens from the database that have addresses, ordered by creation date."""
    try:
        with get_session() as session:
            tokens = session.query(TokenDB)\
                .filter(TokenDB.address.isnot(None))\
                .filter(TokenDB.chain.in_(['base', 'solana']))\
                .order_by(desc(TokenDB.created_at))\
                .options(
                    joinedload(TokenDB.token_reports).joinedload(TokenReportDB.social_media_post),
                    joinedload(TokenDB.token_opportunities)
                )\
                .all()
            
            return [
                {
                    "id": token.id,
                    "symbol": token.symbol,
                    "name": token.name,
                    "chain": str(token.chain),
                    "address": token.address,
                    "created_at": token.created_at.isoformat(),
                    "token_reports": [
                        {
                            "id": report.id,
                            "mentions_purchasable_token": report.mentions_purchasable_token,
                            "token_symbol": report.token_symbol,
                            "token_chain": report.token_chain,
                            "token_address": report.token_address,
                            "is_listed_on_dex": report.is_listed_on_dex,
                            "trading_pairs": report.trading_pairs,
                            "confidence_score": report.confidence_score,
                            "reasoning": report.reasoning,
                            "created_at": report.created_at.isoformat(),
                            "social_media_post": {
                                "id": report.social_media_post.id,
                                "source": report.social_media_post.source,
                                "post_id": report.social_media_post.post_id,
                                "author_id": report.social_media_post.author_id,
                                "author_username": report.social_media_post.author_username,
                                "author_display_name": report.social_media_post.author_display_name,
                                "text": report.social_media_post.text,
                                "original_timestamp": report.social_media_post.original_timestamp.isoformat(),
                                "timestamp": report.social_media_post.timestamp.isoformat(),
                                "reactions_count": report.social_media_post.reactions_count,
                                "replies_count": report.social_media_post.replies_count,
                                "reposts_count": report.social_media_post.reposts_count,
                                "created_at": report.social_media_post.created_at.isoformat()
                            } if report.social_media_post else None
                        }
                        for report in token.token_reports
                    ],
                    "token_opportunities": [
                        {
                            "id": opp.id,
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
                        for opp in token.token_opportunities
                    ]
                }
                for token in tokens
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tokens: {str(e)}"
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
async def get_multi_agent_alpha_scout(token_report: IsTokenReport, token_report_id: int | None = None):
    try:
        # Pass the token report to the alpha scout agent
        token_alpha = await multi_agent_alpha_scout.ainvoke({
            'messages': [token_report.reasoning],
            'token_report': token_report.dict()
        })
        
        with get_session() as session:
            try:
                # If token_report_id is provided, get the TokenReportDB instance and verify it exists
                token_report_db = None
                if token_report_id:
                    token_report_db = session.query(TokenReportDB).get(token_report_id)
                    if not token_report_db:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Token report with ID {token_report_id} not found"
                        )
                    # Ensure the token report is attached to the session
                    session.add(token_report_db)
                
                # Create report in database using the same session
                report_data = {
                    "is_relevant": token_report.mentions_purchasable_token,
                    "analysis": token_report.reasoning,
                    "message": token_report.reasoning,
                    "opportunities": [token_alpha],
                    "token_report_id": token_report_id
                }
                
                db_report = create_alpha_report(report_data, existing_session=session)
                if not db_report:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to save report to database"
                    )
                
                # If we have a token report, ensure relationships are properly established
                if token_report_db and db_report.opportunities:
                    for opportunity in db_report.opportunities:
                        # Ensure bidirectional relationship
                        if opportunity not in token_report_db.opportunities:
                            token_report_db.opportunities.append(opportunity)
                            opportunity.token_report = token_report_db
                
                # Commit all changes in a single transaction
                session.commit()
                
                # Refresh to ensure all relationships are loaded
                session.refresh(db_report)
                if token_report_db:
                    session.refresh(token_report_db)
                    
                    # Verify relationships were properly established
                    if not token_report_db.opportunities:
                        print(f"Warning: Token report {token_report_id} has no opportunities after commit")
                        
                return token_alpha
                
            except Exception as e:
                session.rollback()
                print(f"Database error in get_multi_agent_alpha_scout: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error: {str(e)}"
                )
                
    except Exception as e:
        print(f"Error in get_multi_agent_alpha_scout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/analyze_social_post",
    dependencies=[Depends(api_key_auth)],
    response_model=IsTokenReport | None
)
async def analyze_social_post(input_data: SocialMediaInput, existing_session=None):
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
        
        social_post = create_social_media_post(post_data, existing_session=existing_session)
        if not social_post:
            raise HTTPException(
                status_code=500,
                detail="Failed to save social media post to database"
            )

        # Check if this is an existing post by comparing created_at with current time
        # If the post was created more than 1 minute ago, consider it an existing post
        if (datetime.utcnow() - social_post.created_at).total_seconds() > 15:
            print(f"Skipping analysis - social post {social_post.id} already exists")
            return None

        # For new posts, proceed with analysis
        token_report = await crypto_text_classifier.ainvoke({
            'messages': [input_data.text]
        })

        if not token_report:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze text with token finder agent"
            )

        # Save token report to database and get the saved object
        db_token_report = create_token_report(token_report, social_post.id, existing_session=existing_session)
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
    session = None
    try:
        session = get_session()
        session.__enter__()
        
        # First analyze the social post
        token_report = await analyze_social_post(input_data, existing_session=session)
        
        # If analyze_social_post returns None, it means this is an existing post
        if token_report is None:
            print("Skipping alpha scout - existing social post")
            return None
        
        # Only run alpha scout if:
        # 1. A purchasable token was found
        # 2. The token chain is Base or Solana
        # 3. The token has an address
        # 4. There aren't multiple token reports in the past hour
        if (token_report['mentions_purchasable_token'] and
            token_report.get('token_chain') in ['Base', 'Solana'] and
            token_report.get('token_address')):
            
            # Check for multiple token reports
            if has_recent_token_report(token_report['token_address']):
                print(f"Skipping alpha scout - already ran for token {token_report['token_address']} in the past hour")
                return None
            
            # Create IsTokenReport instance
            token_report_model = IsTokenReport(
                mentions_purchasable_token=token_report['mentions_purchasable_token'],
                token_symbol=token_report['token_symbol'],
                token_chain=token_report['token_chain'],
                token_address=token_report['token_address'],
                is_listed_on_dex=token_report['is_listed_on_dex'],
                trading_pairs=token_report['trading_pairs'],
                confidence_score=token_report['confidence_score'],
                reasoning=token_report['reasoning']
            )
            
            # Call the multi_agent_alpha_scout endpoint with token_report_id
            token_alpha = await get_multi_agent_alpha_scout(token_report_model, token_report['id'])
            return token_alpha
    
        # If no purchasable token found, return None
        return None
        
    except Exception as e:
        if session:
            session.rollback()
        print(f"Error in analyze_and_scout: {str(e)}")  # Add error logging
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if session:
            session.__exit__(None, None, None)
