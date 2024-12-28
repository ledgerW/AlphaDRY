import os
import sys
import argparse
import asyncio
import aiohttp
import random
import logging
from datetime import datetime
from dotenv import load_dotenv
from farcaster import Warpcast

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_social_post.log')
    ]
)

# Change to project root directory if needed
if os.path.basename(os.getcwd()) != os.path.basename(script_dir):
    logging.info(f"Changing directory to: {script_dir}")
    os.chdir(script_dir)

# Load environment variables
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

# Debug environment variables
required_vars = ["MNEMONIC_ENV_VAR", "API_KEY", "API_URL"]
logging.info("Checking environment variables:")
for var in required_vars:
    value = os.environ.get(var)
    # Only show first/last few chars of sensitive values
    if var in ["MNEMONIC_ENV_VAR", "API_KEY"]:
        display_value = f"{value[:8]}...{value[-8:]}" if value else "not set"
    else:
        display_value = value if value else "not set"
    logging.info(f"{var}: {display_value}")

# Verify .env file location
env_path = os.path.abspath('.env')
logging.info(f"Looking for .env file at: {env_path}")
logging.info(f"File exists: {os.path.exists(env_path)}")

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
    'matthew'
]

async def process_cast(session, api_url, headers, cast):
    """Process a single cast through the analyze_social_post endpoint"""
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
        
        # Send to analyze_social_post endpoint
        async with session.post(f"{api_url}/api/analyze_social_post", json=social_media_input, headers=headers) as response:
            response_text = await response.text()
            
            if response.status == 200:
                if response_text == 'null':
                    logging.info("Post already exists in database, skipping...")
                    return None
                    
                logging.info(f"Successfully processed cast. Response: {response_text}")
                return response_text
            else:
                logging.error(f"Error from API: {response.status} - {response_text}")
                return None
    
    except Exception as e:
        logging.error(f"Error processing cast: {e}")
        return None

async def get_random_cast(client):
    """Get a random cast from a random user"""
    try:
        # Pick a random username
        username = random.choice(USERNAMES)
        logging.info(f"Fetching casts for user: {username}")
        
        # Get user info
        user = client.get_user_by_username(username)
        if not user:
            logging.warning(f"Could not find user: {username}")
            return None
        
        # Get user's casts
        casts_response = client.get_casts(user.fid, limit=10)
        if not casts_response or not casts_response.casts:
            logging.warning(f"No casts found for user: {username}")
            return None
        
        # Pick a random cast
        return random.choice(casts_response.casts)
        
    except Exception as e:
        logging.error(f"Error getting random cast: {e}")
        return None

async def test_social_post(num_tests: int = 1):
    """
    Test the analyze_social_post endpoint with random warpcasts
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
    
    env = "dev" if not os.environ.get("REPLIT_DEPLOYMENT") else "prod"
    logging.info(f"Running in {env} environment")
    logging.info(f"Will process {num_tests} random cast(s)")
    
    successful_tests = 0
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_tests):
            logging.info(f"\nTest {i+1}/{num_tests}")
            
            # Get a random cast
            cast = await get_random_cast(client)
            if not cast:
                logging.error("Failed to get random cast")
                continue
            
            # Process the cast
            result = await process_cast(session, api_url, headers, cast)
            if result:
                successful_tests += 1
            
            # Add delay between tests
            if i < num_tests - 1:
                await asyncio.sleep(5)
    
    logging.info(f"\nFinished testing")
    logging.info(f"Successfully processed {successful_tests}/{num_tests} casts")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Test analyze_social_post endpoint with random Warpcasts')
    parser.add_argument('--num', type=int, default=1, help='Number of random casts to test (default: 1)')
    
    args = parser.parse_args()
    
    try:
        # Run the async function
        asyncio.run(test_social_post(num_tests=args.num))
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
