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
                    'market_cap': pair.get('marketCap', None),
                    'image_url': pair.get('info', {}).get('imageUrl'),
                    'website_url': next((w['url'] for w in pair.get('info', {}).get('websites', []) 
                                      if w.get('label') == 'Website'), None),
                    'warpcast_url': next((w['url'] for w in pair.get('info', {}).get('websites', []) 
                                      if w.get('label') == 'Farcaster'), None),
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
    session = existing_session or get_session()
    manage_session = not existing_session
    
    if manage_session:
        session.begin()
    
    try:
        # First try to find existing post
        existing = session.query(SocialMediaPostDB).filter(
            SocialMediaPostDB.post_id == post_data['post_id']
        ).first()
        
        if existing:
            print(f"Found existing post with ID {existing.id} and post_id {existing.post_id}")
            return existing
            
        # If no existing post, create new one
        post = SocialMediaPostDB(**post_data)
        session.add(post)
        session.flush()  # Get the ID
        print(f"Created new post with ID {post.id} and post_id {post.post_id}")
        
        if manage_session:
            session.commit()
            
        return post
        
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating social media post: {str(e)}")
        return None
        
    finally:
        if manage_session:
            session.close()

def get_or_create_token(session, report_data: Dict[str, Any]) -> Optional[TokenDB]:
    """Helper function to get or create a token based on report data."""
    if not (report_data.get('mentions_purchasable_token') and report_data.get('token_chain')):
        return None
        
    chain = report_data['token_chain'].lower()
    
    # Try to find by address first
    if report_data.get('token_address'):
        address = report_data['token_address']
        if chain.lower() != 'solana':
            address = address.lower()
            
        token = session.query(TokenDB).filter(
            TokenDB.chain == chain,
            TokenDB.address == address
        ).first()
        
        if not token and report_data.get('token_symbol'):
            token_data = {
                'symbol': report_data['token_symbol'],
                'name': report_data['token_symbol'],
                'chain': chain,
                'address': address
            }
            
            for field in ['image_url', 'website_url', 'twitter_url', 'telegram_url', 'token_created_at']:
                if report_data.get(field):
                    token_data[field] = report_data[field]
                    
            token = TokenDB(**token_data)
            session.add(token)
            session.flush()
            
    # Try to find by symbol if no address
    elif report_data.get('token_symbol'):
        token = session.query(TokenDB).filter(
            TokenDB.chain == chain,
            TokenDB.symbol == report_data['token_symbol'],
            TokenDB.address.isnot(None)
        ).first()
    
    return token

def create_token_report(report_data: Dict[str, Any], post_id: Optional[int] = None, existing_session=None) -> Optional[TokenReportDB]:
    """Create a new token report with optional association to a social media post and token."""
    session = existing_session or get_session()
    manage_session = not existing_session
    
    if manage_session:
        session.begin()
    
    try:
        # Get or create associated token
        token = get_or_create_token(session, report_data)
        
        # Create token report
        report = TokenReportDB(
            mentions_purchasable_token=report_data.get('mentions_purchasable_token', False),
            token_symbol=report_data.get('token_symbol'),
            token_chain=report_data.get('token_chain', '').lower() if report_data.get('token_chain') else None,
            token_address=report_data.get('token_address'),
            is_listed_on_dex=report_data.get('is_listed_on_dex'),
            trading_pairs=report_data.get('trading_pairs', []),
            confidence_score=report_data.get('confidence_score', 0),
            reasoning=report_data.get('reasoning', ''),
            token_id=token.id if token else None,
            opportunities=[]
        )
        
        session.add(report)
        
        # If we have a post_id, establish the relationship
        if post_id:
            # First try to find by ID
            post = session.query(SocialMediaPostDB).filter(
                SocialMediaPostDB.id == post_id
            ).first()
            
            # If not found by ID, try to find by post_id
            if not post:
                post = session.query(SocialMediaPostDB).filter(
                    SocialMediaPostDB.post_id == str(post_id)
                ).first()
            
            if not post:
                raise ValueError(f"SocialMediaPost with ID/post_id {post_id} not found")
                
            post.token_report = report
            report.social_media_post = post
            
        session.flush()
        
        if manage_session:
            session.commit()
            
        return report
        
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating token report: {str(e)}")
        return None
        
    finally:
        if manage_session:
            session.close()
