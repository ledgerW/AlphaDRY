from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from ..models.base import get_session
from ..models.social import SocialMediaPostDB, TokenReportDB
from ..models.token import TokenDB

async def fetch_dex_screener_data(token_address: str) -> Optional[Dict[str, Any]]:
    """Fetch token data from DEX Screener API and extract relevant fields."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}") as response:
                if response.status != 200:
                    print(f"DEX Screener API error: {response.status}")
                    return None
                    
                data = await response.json()
                
                # Get first pair from response as it's typically the most relevant
                if not data.get('pairs') or len(data['pairs']) == 0:
                    return None
                    
                pair = data['pairs'][0]
                
                # Extract relevant fields
                token_data = {
                    'image_url': pair.get('info', {}).get('imageUrl'),
                    'website_url': next((w['url'] for w in pair.get('info', {}).get('websites', []) 
                                      if w.get('label') == 'Website'), None),
                    'twitter_url': next((s['url'] for s in pair.get('info', {}).get('socials', []) 
                                      if s.get('type') == 'twitter'), None),
                    'telegram_url': next((s['url'] for s in pair.get('info', {}).get('socials', []) 
                                      if s.get('type') == 'telegram'), None),
                    'token_created_at': datetime.fromtimestamp(pair['pairCreatedAt'] / 1000) 
                                      if pair.get('pairCreatedAt') else None
                }
                
                return token_data
    except Exception as e:
        print(f"Error fetching DEX Screener data: {e}")
        return None


def create_social_media_post(post_data: Dict[str, Any], existing_session=None) -> Optional[SocialMediaPostDB]:
    """Create a new social media post entry or return existing one."""
    if existing_session:
        session = existing_session
        manage_session = False
    else:
        session = get_session()
        manage_session = True
        
    if manage_session:
        session.__enter__()
        
    try:
        # Use get() or create pattern with explicit transaction
        with session.begin_nested():
            try:
                # Try to create new post first
                post = SocialMediaPostDB(**post_data)
                session.add(post)
                session.flush()
                return post
            except IntegrityError:
                # If unique constraint violation, rollback the nested transaction
                session.rollback()
                # Then try to get existing post
                existing = session.query(SocialMediaPostDB).filter(
                    SocialMediaPostDB.post_id == post_data['post_id']
                ).first()
                if existing:
                    return existing
                raise  # Re-raise if we couldn't find the existing post
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating social media post: {e}")
        return None
    finally:
        if manage_session:
            session.__exit__(None, None, None)

def create_token_report(report_data: Dict[str, Any], post_id: Optional[int] = None, existing_session=None) -> Optional[TokenReportDB]:
    """Create a new token report with optional association to a social media post and token."""
    if existing_session:
        session = existing_session
        manage_session = False
    else:
        session = get_session()
        manage_session = True
        
    if manage_session:
        session.__enter__()
        
    try:
        # Try to find or create token if this is a purchasable token
        token = None
        chain = None
        if report_data.get('mentions_purchasable_token') and report_data.get('token_chain'):
            chain = report_data['token_chain'].lower()
            
            # First try to find/create by address if available
            if report_data.get('token_address'):
                # Normalize address case based on chain
                address = report_data['token_address']
                if chain.lower() != 'solana':
                    address = address.lower()
                
                # Exact address matching since we've normalized the case
                token = session.query(TokenDB).filter(
                    TokenDB.chain == chain,
                    TokenDB.address == address
                ).first()
                
                if not token and report_data.get('token_symbol'):
                    # Create new token with address and additional data if available
                    token_data = {
                        'symbol': report_data['token_symbol'],
                        'name': report_data['token_symbol'],  # Use symbol as name initially
                        'chain': chain,
                        'address': address  # Use normalized address
                    }
                    
                    # Add any additional token data if provided
                    for field in ['image_url', 'website_url', 'twitter_url', 'telegram_url', 'token_created_at']:
                        if report_data.get(field):
                            token_data[field] = report_data[field]
                            
                    try:
                        token = TokenDB(**token_data)
                        session.add(token)
                        session.flush()  # Get token ID
                    except IntegrityError:
                        # Token already exists (race condition), fetch it
                        session.rollback()
                        token = session.query(TokenDB).filter(
                            TokenDB.chain == chain,
                            TokenDB.address == address
                        ).first()
                        if not token:
                            raise  # Re-raise if we couldn't find the token
            
            # If no address available, try to find by symbol and chain, but only match with tokens that have addresses
            elif report_data.get('token_symbol'):
                # Try to find existing token by symbol and chain that has an address
                token = session.query(TokenDB).filter(
                    TokenDB.chain == chain,
                    TokenDB.symbol == report_data['token_symbol'],
                    TokenDB.address.isnot(None)  # Only match with tokens that have addresses
                ).first()
                
                # Don't create new token if we don't have an address
        
        # Create token report with explicit field mapping
        report = TokenReportDB(
            mentions_purchasable_token=report_data.get('mentions_purchasable_token', False),
            token_symbol=report_data.get('token_symbol'),
            token_chain=None if not chain else chain,
            token_address=report_data.get('token_address'),
            is_listed_on_dex=report_data.get('is_listed_on_dex'),
            trading_pairs=report_data.get('trading_pairs', []),
            confidence_score=report_data.get('confidence_score', 0),
            reasoning=report_data.get('reasoning', ''),
            token_id=token.id if token else None
        )
        
        # If post_id provided, establish bidirectional relationship
        if post_id:
            post = session.get(SocialMediaPostDB, post_id)
            if post:
                report.social_media_post = post
                post.token_report = report
            else:
                print(f"Warning: SocialMediaPost with ID {post_id} not found")
        
        # Initialize empty opportunities list
        report.opportunities = []
        
        try:
            # Use get() or create pattern with explicit transaction
            with session.begin_nested():
                try:
                    session.add(report)
                    session.flush()
                    session.refresh(report)
                    return report
                except IntegrityError:
                    # If unique constraint violation, rollback the nested transaction
                    session.rollback()
                    # Try to find an existing report with the same token and post
                    if post_id:
                        existing_report = session.query(TokenReportDB).filter(
                            TokenReportDB.token_id == (token.id if token else None),
                            TokenReportDB.social_media_post_id == post_id
                        ).first()
                        if existing_report:
                            return existing_report
                    raise  # Re-raise if we couldn't find an existing report
        except Exception as e:
            if manage_session:
                session.rollback()
            print(f"Error creating token report: {e}")
            return None
    finally:
        if manage_session:
            session.__exit__(None, None, None)
