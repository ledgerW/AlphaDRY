import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import desc, func, and_, or_, not_, select

from chains.seek_alpha_chain import base_seek_alpha, multi_hop_seek_alpha
from chains.alpha_chain import Alpha
from chains.social_summary_chain import social_summary_chain
from agents.multi_agent_alpha_scout import multi_agent_alpha_scout
from agents.multi_agent_token_finder import crypto_text_classifier
from agents.models import TokenAlpha
from agents.tools import IsTokenReport
from database import (
    create_alpha_report, TokenReportDB, get_session,
    create_social_media_post, create_token_report
)
from db.operations.alpha import has_recent_token_report
from db.operations.social import fetch_dex_screener_data
from .api_models import Token, SocialMediaInput
from schemas import SocialMediaSummary
from db.models.token import TokenDB

load_dotenv()

header_scheme = APIKeyHeader(name="x-key")

def api_key_auth(api_key: str = Depends(header_scheme)):
    if api_key != os.environ['API_KEY']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )

router = APIRouter(tags=["generation"])

@router.get(
    "/token/social_summary/{token_address}",
    dependencies=[Depends(api_key_auth)],
    response_model=SocialMediaSummary
)
async def get_token_social_summary(token_address: str):
    """Get a summary of all social media posts related to a token"""
    try:
        with get_session() as session:
            # Get token from database (case-sensitive for Solana, case-insensitive for others)
            token = session.query(TokenDB).filter(
                sa.or_(
                    # For Solana: exact match
                    sa.and_(TokenDB.chain == 'solana', TokenDB.address == token_address),
                    # For other chains: case-insensitive match
                    sa.and_(TokenDB.chain != 'solana', func.lower(TokenDB.address) == token_address.lower())
                )
            ).first()
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail=f"Token with address {token_address} not found"
                )
            
            # Get all social media posts through token reports with full details
            social_posts = []
            for report in token.token_reports:
                if report.social_media_post:
                    post = report.social_media_post
                    formatted_post = (
                        f"Source: {post.source}\n"
                        f"Author: {post.author_display_name or post.author_username} (@{post.author_username})\n"
                        f"Time: {post.original_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                        f"Content: {post.text}\n"
                        f"Engagement: {post.reactions_count} reactions, {post.replies_count} replies, {post.reposts_count} reposts\n"
                        f"---\n"
                    )
                    social_posts.append(formatted_post)
            
            if not social_posts:
                return SocialMediaSummary(
                    summary="No social media posts found for this token.",
                    total_posts=0
                )
            
            # Generate summary using LLM chain with detailed post information
            summary_result = await social_summary_chain.ainvoke({
                "posts": "\n".join(social_posts)
            })
            
            return SocialMediaSummary(
                summary=summary_result,  # summary_result is already the text content
                total_posts=len(social_posts)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def get_multi_agent_alpha_scout(data: dict):
    try:
        # Extract token_report and token_report_id from request data
        if 'token_report' not in data:
            raise HTTPException(status_code=400, detail="token_report is required")
        
        # Create IsTokenReport instance from the data
        token_report = IsTokenReport(**data['token_report'])
        token_report_id = data.get('token_report_id')
        
        # Get social media summary if token address is available
        social_media_summary = None
        if token_report.token_address:
            try:
                social_summary = await get_token_social_summary(token_report.token_address)
                social_media_summary = f"Total Posts: {social_summary.total_posts}\n\n{social_summary.summary}"
            except HTTPException as e:
                if e.status_code != 404:  # Ignore 404s, but log other errors
                    print(f"Error fetching social summary: {str(e)}")
                pass
        
        # Pass the token report and social summary to the alpha scout agent
        token_alpha = await multi_agent_alpha_scout.ainvoke({
            'messages': [token_report.reasoning],
            'token_report': token_report.dict(),
            'social_media_summary': social_media_summary
        })
        
        if not token_alpha:
            raise HTTPException(
                status_code=500,
                detail="Alpha scout analysis returned no results"
            )
            
        # Ensure we have a valid TokenAlpha object
        if not isinstance(token_alpha, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid alpha scout result format"
            )
            
        print("Alpha scout result:", token_alpha)  # Debug log
        
        # Save results to database
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
                    
                    # Refresh token to ensure opportunities are loaded
                    if token_report_db.token:
                        session.refresh(token_report_db.token)
                        
                # Return the token alpha result
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
            "reactions_count": input_data.reactions_count,
            "replies_count": input_data.replies_count,
            "reposts_count": input_data.reposts_count,
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

        # If we have a token address, fetch additional data from DEX Screener
        if token_report.get('token_address'):
            dex_data = await fetch_dex_screener_data(token_report['token_address'])
            if dex_data:
                token_report.update(dex_data)
        
        # Save token report to database and get the saved object
        db_token_report = create_token_report(token_report, social_post.id, existing_session=existing_session)
        if not db_token_report:
            raise HTTPException(
                status_code=500,
                detail="Failed to save token report to database"
            )

        # If we're managing our own session, commit the transaction
        if not existing_session:
            session = get_session()
            with session.begin():
                session.merge(social_post)
                session.merge(db_token_report)
                session.commit()

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
            token_alpha = await get_multi_agent_alpha_scout({
                'token_report': token_report_model.dict(),
                'token_report_id': token_report['id']
            })
            return token_alpha
    
        # If no purchasable token found, return None
        return None
        
    except Exception as e:
        if session:
            session.rollback()
        print(f"Error in analyze_and_scout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if session:
            session.__exit__(None, None, None)
