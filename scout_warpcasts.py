import os
import sys
import argparse
import asyncio
import aiohttp
from datetime import datetime
from farcaster import Warpcast
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scout_warpcasts.log')
    ]
)

# List of usernames to fetch casts from
USERNAMES = [
    'ace',
    'jessepollak',
    'halfmaxxing',
    'jacek',
    'deployer',
    'mleejr',
    'df',
    'wake.eth',
    'sartocrates',
    'carlos',
    'birtcon',
    'matthew'
]

async def process_cast(session, api_url, headers, cast, client, total_processed, total_opportunities):
    """Process a single cast"""
    try:
        # Add 5 second delay before processing
        await asyncio.sleep(5)
        
        # Create social media input object
        cast_dict = cast.dict()
        social_media_input = {
            "text": cast_dict.get('text', ''),
            "source": "warpcast",
            "author_id": str(cast_dict.get('author', {}).get('fid', '')),
            "author_username": cast_dict.get('author', {}).get('username', ''),
            "author_display_name": cast_dict.get('author', {}).get('display_name', ''),
            "post_id": cast_dict.get('hash', ''),
            "original_timestamp": cast_dict.get('timestamp', datetime.utcnow().isoformat())
        }
        
        # Send to analyze_and_scout endpoint
        async with session.post(f"{api_url}/api/analyze_and_scout", json=social_media_input, headers=headers) as response:
            if response.status == 200:
                total_processed[0] += 1
                response_data = await response.json()
                
                # Check if any opportunities were found
                if response_data:
                    total_opportunities[0] += 1
                    logging.info(f"Found opportunity in cast: {cast_dict.get('text', '')[:100]}...")
                
                return True
            else:
                response_text = await response.text()
                logging.error(f"Error from API: {response.status} - {response_text}")
                return False
    
    except Exception as e:
        logging.error(f"Error processing cast: {e}")
        return False

async def process_user(session, api_url, headers, username, client, total_casts_target, total_processed, total_opportunities):
    """Process casts for a single user"""
    try:
        logging.info(f"\nProcessing user: {username}")
        
        # Get user info
        user = client.get_user_by_username(username)
        if not user:
            logging.warning(f"Could not find user: {username}")
            return 0, 0
        
        # Get user's casts
        casts_response = client.get_casts(user.fid, limit=10)
        if not casts_response or not casts_response.casts:
            logging.warning(f"No casts found for user: {username}")
            return 0, 0
        
        user_casts_processed = 0
        user_opportunities_found = 0
        
        # Process casts sequentially to maintain 5-second buffer between API calls
        for cast in casts_response.casts:
            if total_processed[0] >= total_casts_target:
                break
                
            success = await process_cast(session, api_url, headers, cast, client, total_processed, total_opportunities)
            if success:
                user_casts_processed += 1
        
        logging.info(f"Processed {user_casts_processed} casts for {username}")
        return user_casts_processed, user_opportunities_found
        
    except Exception as e:
        logging.error(f"Error processing user {username}: {e}")
        return 0, 0

async def scout_warpcasts(test_mode: bool = False):
    """
    Fetch recent warpcasts and send them to the analyze_and_scout endpoint
    """
    # Get required environment variables
    mnemonic = os.environ.get("MNEMONIC_ENV_VAR")
    api_key = os.environ.get("API_KEY")
    api_url = os.environ.get("API_URL")
    
    if not mnemonic or not api_key or not api_url:
        logging.error("Required environment variables MNEMONIC_ENV_VAR, API_KEY, or API_URL not set")
        sys.exit(1)
    
    # Initialize Warpcast client
    client = Warpcast(mnemonic=mnemonic)
    
    # Test API connection
    try:
        client.get_healthcheck()
    except Exception as e:
        logging.error(f"Error connecting to Warpcast API: {e}")
        sys.exit(1)
    
    # Set up API headers
    headers = {
        "x-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Set parameters based on test mode
    total_casts_target = 3 if test_mode else len(USERNAMES) * 10
    
    # Use lists to allow modification in nested functions
    total_processed = [0]
    total_opportunities = [0]
    
    env = "dev" if not os.environ.get("REPLIT_DEPLOYMENT") else "prod"
    logging.info(f"Running in {env} environment")
    logging.info(f"Target number of casts to process: {total_casts_target}")
    
    async with aiohttp.ClientSession() as session:
        # Process users sequentially to maintain 5-second buffer between API calls
        for username in USERNAMES:
            if total_processed[0] >= total_casts_target:
                break
            
            await process_user(
                session, api_url, headers, username, client,
                total_casts_target, total_processed, total_opportunities
            )
    
    logging.info(f"\nFinished processing {total_processed[0]} casts")
    logging.info(f"Found {total_opportunities[0]} total opportunities")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Scout Warpcasts for opportunities')
    parser.add_argument('--test', action='store_true', help='Run in test mode (process only 3 casts total)')
    
    args = parser.parse_args()
    
    try:
        # Run the async function
        asyncio.run(scout_warpcasts(test_mode=args.test))
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
