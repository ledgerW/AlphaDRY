"""Token database operations"""
from typing import Dict, Optional
from sqlalchemy import or_, and_, func
from ..models.token import TokenDB

def get_or_create_token(session, token_report: Dict) -> Optional[TokenDB]:
    """Get an existing token or create a new one based on token report data.
    
    Args:
        session: SQLAlchemy session
        token_report: Dictionary containing token information from report
        
    Returns:
        TokenDB instance if successful, None if required data is missing
    """
    if not token_report.get('token_chain') or not token_report.get('token_symbol'):
        return None
        
    # Try to find existing token
    token = None
    if token_report.get('token_address'):
        # Handle case sensitivity for Solana addresses
        if token_report['token_chain'].lower() == 'solana':
            token = session.query(TokenDB).filter(
                and_(
                    TokenDB.chain == token_report['token_chain'],
                    TokenDB.address == token_report['token_address']
                )
            ).first()
        else:
            # Case insensitive match for other chains
            token = session.query(TokenDB).filter(
                and_(
                    TokenDB.chain == token_report['token_chain'],
                    func.lower(TokenDB.address) == token_report['token_address'].lower()
                )
            ).first()
    
    # If no token found by address, try to find by chain and symbol
    if not token:
        token = session.query(TokenDB).filter(
            and_(
                TokenDB.chain == token_report['token_chain'],
                TokenDB.symbol == token_report['token_symbol']
            )
        ).first()
    
    # Create new token if none found
    if not token:
        token = TokenDB(
            symbol=token_report['token_symbol'],
            name=token_report.get('token_name', token_report['token_symbol']),
            chain=token_report['token_chain'],
            address=token_report.get('token_address'),
            website_url=token_report.get('website_url'),
            twitter_url=token_report.get('twitter_url'),
            telegram_url=token_report.get('telegram_url'),
            warpcast_url=token_report.get('warpcast_url'),
            signal_url=token_report.get('signal_url'),
            image_url=token_report.get('image_url'),
            token_created_at=token_report.get('token_created_at')
        )
        session.add(token)
        session.flush()  # Get ID without committing
        
    return token
