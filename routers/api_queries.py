from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func, and_, or_, not_

from database import (
    TokenDB, AlphaReportDB, TokenOpportunityDB, TokenReportDB, 
    SocialMediaPostDB, get_session
)
from .api_models import AlphaReport, TokenOpportunity, TokenData

router = APIRouter(tags=["queries"])

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
            # For Base/ETH addresses use case-insensitive comparison, for Solana use exact match
            token = session.query(TokenDB)\
                .filter(
                    # If address starts with 0x, use case-insensitive match (Base/ETH)
                    # Otherwise use exact match (Solana)
                    or_(
                        and_(
                            TokenDB.address.startswith('0x'),
                            func.lower(TokenDB.address) == func.lower(address)
                        ),
                        and_(
                            not_(TokenDB.address.startswith('0x')),
                            TokenDB.address == address
                        )
                    )
                )\
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
