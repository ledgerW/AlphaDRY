from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import desc, func, and_, or_, not_, select, literal

from database import (
    TokenDB, AlphaReportDB, TokenOpportunityDB, TokenReportDB, 
    SocialMediaPostDB, get_session
)
from datetime import datetime
from .api_models import AlphaReport, TokenOpportunity, TokenData

router = APIRouter(tags=["queries"])

@router.get("/latest_warpcast/{username}")
async def get_latest_warpcast(username: str):
    """Get the timestamp of the latest processed warpcast for a user"""
    try:
        with get_session() as session:
            # Query for the latest post by this user
            post = session.query(SocialMediaPostDB).filter(
                SocialMediaPostDB.author_username == username,
                SocialMediaPostDB.source == "warpcast"
            ).order_by(desc(SocialMediaPostDB.original_timestamp)).first()
            
            if post:
                return {
                    "username": username,
                    "latest_timestamp": post.original_timestamp.isoformat(),
                    "post_id": post.post_id
                }
            
            # If no posts found, return a very old date
            return {
                "username": username,
                "latest_timestamp": datetime(2000, 1, 1).isoformat(),
                "post_id": None
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest warpcast: {str(e)}"
        )

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
                                address=opp.token.address,
                                image_url=opp.token.image_url,
                                website_url=opp.token.website_url,
                                warpcast_url=opp.token.warpcast_url,
                                twitter_url=opp.token.twitter_url,
                                telegram_url=opp.token.telegram_url,
                                signal_url=opp.token.signal_url
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
                "image_url": token.image_url,
                "website_url": token.website_url,
                "warpcast_url": token.warpcast_url,
                "twitter_url": token.twitter_url,
                "telegram_url": token.telegram_url,
                "signal_url": token.signal_url,
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
async def get_tokens(
    cursor: Optional[str] = None,
    per_page: int = 10,
    chains: Optional[str] = None,
    market_cap_max: Optional[float] = None,
    sort_by: Optional[str] = None
):
    """Get filtered and sorted tokens from the database."""
    try:
        with get_session() as session:
            # Base query with joins
            query = session.query(TokenDB)\
                .filter(TokenDB.address.isnot(None))

            # Apply chain filter
            if chains:
                selected_chains = [c.lower() for c in chains.split(',')]
                query = query.filter(func.lower(TokenDB.chain).in_(selected_chains))
            else:
                # Default to base and solana if no chains specified
                query = query.filter(func.lower(TokenDB.chain).in_(['base', 'solana']))

            # Create opportunities subquery if needed for market cap filtering or sorting
            if market_cap_max is not None or sort_by in ['recent_opportunity', 'market_cap']:
                opp_subquery = (
                    session.query(
                        TokenOpportunityDB.token_id,
                        func.max(TokenOpportunityDB.created_at).label('max_created_at'),
                        func.max(TokenOpportunityDB.market_cap).label('max_market_cap')
                    )
                    .group_by(TokenOpportunityDB.token_id)
                    .subquery()
                )
                query = query.outerjoin(opp_subquery, TokenDB.id == opp_subquery.c.token_id)

                # Apply market cap filter if specified
                if market_cap_max is not None:
                    query = query.filter(
                        or_(
                            opp_subquery.c.max_market_cap.is_(None),
                            opp_subquery.c.max_market_cap <= market_cap_max
                        )
                    )

            # Create additional subqueries for sorting if needed
            if sort_by == 'kol_events':
                # Subquery for KOL events
                kol_subquery = (
                    session.query(
                        TokenReportDB.token_id,
                        (func.count(TokenReportDB.id) +
                         func.coalesce(func.sum(SocialMediaPostDB.reactions_count), 0) +
                         func.coalesce(func.sum(SocialMediaPostDB.replies_count), 0) +
                         func.coalesce(func.sum(SocialMediaPostDB.reposts_count), 0)
                        ).label('total_events')
                    )
                    .outerjoin(TokenReportDB.social_media_post)
                    .group_by(TokenReportDB.token_id)
                    .subquery()
                )
                query = query.outerjoin(kol_subquery, TokenDB.id == kol_subquery.c.token_id)

            elif sort_by == 'recent_social':
                # Subquery for recent social posts
                social_subquery = (
                    session.query(
                        TokenReportDB.token_id,
                        func.max(SocialMediaPostDB.timestamp).label('max_timestamp')
                    )
                    .join(TokenReportDB.social_media_post)
                    .group_by(TokenReportDB.token_id)
                    .subquery()
                )
                query = query.outerjoin(social_subquery, TokenDB.id == social_subquery.c.token_id)

            # Apply cursor-based pagination
            if cursor:
                cursor_data = cursor.split('_')
                if sort_by == 'market_cap':
                    market_cap_value = float(cursor_data[0]) if cursor_data[0] != 'null' else None
                    token_id = int(cursor_data[1])
                    if market_cap_value is None:
                        query = query.filter(
                            or_(
                                opp_subquery.c.max_market_cap.isnot(None),
                                and_(
                                    opp_subquery.c.max_market_cap.is_(None),
                                    TokenDB.id > token_id
                                )
                            )
                        )
                    else:
                        query = query.filter(
                            or_(
                                opp_subquery.c.max_market_cap < market_cap_value,
                                and_(
                                    opp_subquery.c.max_market_cap == market_cap_value,
                                    TokenDB.id > token_id
                                )
                            )
                        )

                elif sort_by == 'recent_opportunity':
                    timestamp = datetime.fromisoformat(cursor_data[0])
                    token_id = int(cursor_data[1])
                    query = query.filter(
                        or_(
                            opp_subquery.c.max_created_at < timestamp,
                            and_(
                                opp_subquery.c.max_created_at == timestamp,
                                TokenDB.id > token_id
                            )
                        )
                    )

                elif sort_by == 'kol_events':
                    events = int(cursor_data[0])
                    token_id = int(cursor_data[1])
                    query = query.filter(
                        or_(
                            kol_subquery.c.total_events < events,
                            and_(
                                kol_subquery.c.total_events == events,
                                TokenDB.id > token_id
                            )
                        )
                    )

                elif sort_by == 'recent_social':
                    timestamp = datetime.fromisoformat(cursor_data[0])
                    token_id = int(cursor_data[1])
                    query = query.filter(
                        or_(
                            social_subquery.c.max_timestamp < timestamp,
                            and_(
                                social_subquery.c.max_timestamp == timestamp,
                                TokenDB.id > token_id
                            )
                        )
                    )

                else:
                    timestamp = datetime.fromisoformat(cursor_data[0])
                    token_id = int(cursor_data[1])
                    query = query.filter(
                        or_(
                            TokenDB.created_at < timestamp,
                            and_(
                                TokenDB.created_at == timestamp,
                                TokenDB.id > token_id
                            )
                        )
                    )

            # Apply sorting and related filters
            if sort_by == 'recent_opportunity':
                # Only include tokens that have opportunities
                query = query.filter(opp_subquery.c.max_created_at.isnot(None))
                query = query.order_by(desc(opp_subquery.c.max_created_at))
            elif sort_by == 'market_cap':
                # Only include tokens that have market cap data
                query = query.filter(opp_subquery.c.max_market_cap.isnot(None))
                query = query.order_by(desc(opp_subquery.c.max_market_cap))
            elif sort_by == 'kol_events':
                # Only include tokens that have KOL events
                query = query.filter(kol_subquery.c.total_events > 0)
                query = query.order_by(desc(kol_subquery.c.total_events))
            elif sort_by == 'recent_social':
                # Only include tokens that have social media posts
                query = query.filter(social_subquery.c.max_timestamp.isnot(None))
                query = query.order_by(desc(social_subquery.c.max_timestamp))
            else:
                query = query.order_by(desc(TokenDB.created_at))

            # Fetch tokens with relationships
            tokens = query\
                .limit(per_page + 1)\
                .options(
                    selectinload(TokenDB.token_reports).selectinload(TokenReportDB.social_media_post),
                    selectinload(TokenDB.token_opportunities)
                )\
                .all()

            # Check if there are more tokens
            has_more = len(tokens) > per_page
            if has_more:
                tokens = tokens[:-1]  # Remove the extra token we fetched

            # Generate next cursor
            next_cursor = None
            if has_more and tokens:
                last_token = tokens[-1]
                if sort_by == 'market_cap':
                    last_market_cap = max((opp.market_cap for opp in last_token.token_opportunities if opp.market_cap is not None), default=None)
                    next_cursor = f"{str(last_market_cap) if last_market_cap is not None else 'null'}_{last_token.id}"
                elif sort_by == 'recent_opportunity':
                    last_opp_date = max((opp.created_at for opp in last_token.token_opportunities), default=last_token.created_at)
                    next_cursor = f"{last_opp_date.isoformat()}_{last_token.id}"
                elif sort_by == 'kol_events':
                    last_events = sum(1 + (report.social_media_post.reactions_count or 0) + 
                                   (report.social_media_post.replies_count or 0) + 
                                   (report.social_media_post.reposts_count or 0)
                                   for report in last_token.token_reports if report.social_media_post)
                    next_cursor = f"{last_events}_{last_token.id}"
                elif sort_by == 'recent_social':
                    last_social = max((report.social_media_post.timestamp for report in last_token.token_reports 
                                    if report.social_media_post), default=last_token.created_at)
                    next_cursor = f"{last_social.isoformat()}_{last_token.id}"
                else:
                    next_cursor = f"{last_token.created_at.isoformat()}_{last_token.id}"

            # Convert tokens to response format
            token_list = [
                {
                    "id": token.id,
                    "symbol": token.symbol,
                    "name": token.name,
                    "chain": str(token.chain),
                    "address": token.address,
                    "created_at": token.created_at.isoformat(),
                    "image_url": token.image_url,
                    "website_url": token.website_url,
                    "warpcast_url": token.warpcast_url,
                    "twitter_url": token.twitter_url,
                    "telegram_url": token.telegram_url,
                    "signal_url": token.signal_url,
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
            
            return {
                "tokens": token_list,
                "next_cursor": next_cursor,
                "has_more": has_more
            }
    except Exception as e:
        print(f"Error in get_tokens: {str(e)}")  # Add detailed logging
        print(f"Request parameters - cursor: {cursor}, sort_by: {sort_by}, chains: {chains}, market_cap_max: {market_cap_max}")
        if cursor:
            try:
                cursor_data = cursor.split('_')
                print(f"Cursor data: {cursor_data}")
            except Exception as cursor_error:
                print(f"Error parsing cursor: {cursor_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tokens: {str(e)}"
        )
