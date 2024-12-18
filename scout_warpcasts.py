import os
import sys
import requests
import argparse
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
    'halfmaxxing',
    'deployer',
    'mleejr',
    'df',
    'wake.eth',
    'sartocrates',
    'oi',
    'carlos',
    'birtcon',
    'matthew',
    'jacek'
]

def scout_warpcasts(test_mode: bool = False):
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
    total_casts_target = 3 if test_mode else len(USERNAMES) * 20
    casts_per_user = 20
    
    total_casts_processed = 0
    total_opportunities_found = 0
    
    env = "dev" if not os.environ.get("REPLIT_DEPLOYMENT") else "prod"
    logging.info(f"Running in {env} environment")
    logging.info(f"Target number of casts to process: {total_casts_target}")
    
    for username in USERNAMES:
        if total_casts_processed >= total_casts_target:
            break
            
        try:
            logging.info(f"\nProcessing user: {username}")
            
            # Get user info
            user = client.get_user_by_username(username)
            if not user:
                logging.warning(f"Could not find user: {username}")
                continue
            
            # Get user's casts
            casts_response = client.get_casts(user.fid, limit=casts_per_user)
            if not casts_response or not casts_response.casts:
                logging.warning(f"No casts found for user: {username}")
                continue
            
            user_casts_processed = 0
            user_opportunities_found = 0
            
            for cast in casts_response.casts:
                if total_casts_processed >= total_casts_target:
                    break
                    
                try:
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
                    response = requests.post(f"{api_url}/api/analyze_and_scout", json=social_media_input, headers=headers)
                    
                    if response.status_code == 200:
                        user_casts_processed += 1
                        total_casts_processed += 1
                        
                        # Check if any opportunities were found
                        if response.json():
                            user_opportunities_found += 1
                            total_opportunities_found += 1
                            logging.info(f"Found opportunity in cast: {cast_dict.get('text', '')[:100]}...")
                    else:
                        logging.error(f"Error from API: {response.status_code} - {response.text}")
                
                except Exception as e:
                    logging.error(f"Error processing cast: {e}")
                    continue
            
            logging.info(f"Processed {user_casts_processed} casts for {username}")
            logging.info(f"Found {user_opportunities_found} opportunities in {username}'s casts")
            
        except Exception as e:
            logging.error(f"Error processing user {username}: {e}")
            continue
    
    logging.info(f"\nFinished processing {total_casts_processed} casts")
    logging.info(f"Found {total_opportunities_found} total opportunities")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Scout Warpcasts for opportunities')
    parser.add_argument('--test', action='store_true', help='Run in test mode (process only 3 casts total)')
    
    args = parser.parse_args()
    
    try:
        scout_warpcasts(test_mode=args.test)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
