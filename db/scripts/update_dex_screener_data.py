#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import from db package
sys.path.append(str(Path(__file__).parent.parent.parent))

from db.models.token import TokenDB
from db.models.base import get_session
from db.operations.social import fetch_dex_screener_data

async def update_tokens_with_dex_data():
    """Update all tokens with data from DEX Screener."""
    session = get_session()
    
    try:
        # Get all tokens that have addresses
        tokens = session.query(TokenDB).filter(TokenDB.address.isnot(None)).all()
        print(f"Found {len(tokens)} tokens with addresses")
        
        for token in tokens:
            print(f"Fetching data for {token.symbol} ({token.address})")
            
            # Fetch data from DEX Screener
            dex_data = await fetch_dex_screener_data(token.address)
            
            if dex_data:
                print(f"Updating {token.symbol} with new data")
                # Update token fields
                token.image_url = dex_data.get('image_url') or token.image_url
                token.website_url = dex_data.get('website_url') or token.website_url
                token.warpcast_url = dex_data.get('warpcast_url') or token.warpcast_url
                token.twitter_url = dex_data.get('twitter_url') or token.twitter_url
                token.telegram_url = dex_data.get('telegram_url') or token.telegram_url
                token.token_created_at = dex_data.get('token_created_at') or token.token_created_at
            else:
                print(f"No data found for {token.symbol}")
        
        # Commit all changes
        session.commit()
        print("Successfully updated tokens with DEX Screener data")
        
    except Exception as e:
        print(f"Error updating tokens: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(update_tokens_with_dex_data())
