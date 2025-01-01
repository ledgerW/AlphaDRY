#!/usr/bin/env python3
import os
import sys
import argparse

# Process environment arguments first
parser = argparse.ArgumentParser(description='Scout Warpcasts for opportunities')
parser.add_argument('--test', action='store_true', help='Run in test mode (process only 3 casts total)')
parser.add_argument('--prod', action='store_true', help='Run against production database tables (prod_ prefix)')
args = parser.parse_args()

# Set environment before importing any database models
if args.prod:
    os.environ["REPLIT_DEPLOYMENT"] = "1"
else:
    os.environ["REPLIT_DEPLOYMENT"] = "0"

import asyncio
import aiohttp
from datetime import datetime
from farcaster import Warpcast
from dotenv import load_dotenv
import logging
from sqlalchemy import select, desc
from db.connection import get_engine
from db.models.social import SocialMediaPostDB
from sqlalchemy.orm import Session

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

# Log environment and verify table prefix
env = "prod" if args.prod else "dev"
logging.info(f"Running against {env} database tables ({env}_prefix)")

# Verify table prefix by checking the model's __tablename__
table_name = SocialMediaPostDB.__tablename__
if not table_name.startswith(f"{env}_"):
    logging.error(f"Incorrect table prefix! Expected {env}_ but got {table_name}")
    sys.exit(1)
logging.info(f"Verified table name: {table_name}")

PRIMARY_USER = 'drypowder'
PRIMARY_USER_FID = 887822
#PRIMARY_USER = 'ledgerwest.eth'
#PRIMARY_USER_FID = 383351

async def get_following_usernames(client):
    """Get list of usernames that PRIMARY_USER is following"""
    try:
        following = client.get_following(PRIMARY_USER_FID, limit=100)
        if not following:
            logging.warning(f"No following found for user: {PRIMARY_USER}")
            return []
        
        # Extract usernames from user objects
        usernames = [user.username for user in following.users if user.username]
        logging.info(f"Found {len(usernames)} users that {PRIMARY_USER} is following")
        return usernames
    except Exception as e:
        logging.error(f"Error getting following list: {e}")
        return []


async def process_cast(session, api_url, headers, cast, client, total_processed, total_opportunities):
    """Process a single cast"""
    try:
        # Add 5 second delay before processing
        await asyncio.sleep(5)
        
        # Create social media input object
        cast_dict = cast.dict()
        
        # Convert timestamp to ISO format (convert from milliseconds to seconds)
        try:
            default_ts = int(datetime.utcnow().timestamp() * 1000)  # Default in milliseconds
            timestamp = datetime.fromtimestamp(cast_dict.get('timestamp', default_ts) / 1000)
            original_timestamp = timestamp.isoformat()
        except Exception as e:
            logging.error(f"Error converting timestamp: {e}")
            original_timestamp = datetime.utcnow().isoformat()
        
        social_media_input = {
            "text": cast_dict.get('text', ''),
            "source": "warpcast",
            "author_id": str(cast_dict.get('author', {}).get('fid', '')),
            "author_username": cast_dict.get('author', {}).get('username', ''),
            "author_display_name": cast_dict.get('author', {}).get('display_name', ''),
            "post_id": cast_dict.get('hash', ''),
            "original_timestamp": original_timestamp,
            "replies_count": cast_dict.get('replies', {}).get('count', 0),
            "reactions_count": cast_dict.get('reactions', {}).get('count', 0),
            "recasts_count": cast_dict.get('recasts', {}).get('count', 0)
        }
        
        # Send to analyze_social_post endpoint
        async with session.post(f"{api_url}/api/analyze_social_post", json=social_media_input, headers=headers) as response:
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

def get_latest_post_timestamp(username: str) -> datetime:
    """Get the timestamp of the latest processed post for a user"""
    try:
        # Get a fresh engine instance to ensure we use the current environment
        engine = get_engine()
        logging.info(f"Using database engine with table prefix: {SocialMediaPostDB.__tablename__}")
        with Session(engine) as db_session:
            # Query for the latest post by this user
            query = select(SocialMediaPostDB).where(
                SocialMediaPostDB.author_username == username,
                SocialMediaPostDB.source == "warpcast"
            ).order_by(desc(SocialMediaPostDB.original_timestamp)).limit(1)
            
            # Log the raw SQL query for debugging
            compiled_query = query.compile(compile_kwargs={"literal_binds": True})
            logging.info(f"Executing query for {username}: {compiled_query}")
            result = db_session.execute(query).first()
            
            if result:
                # Access the SocialMediaPostDB object and its original_timestamp field
                post = result[0]
                logging.info(f"Found post for {username}:")
                logging.info(f"  - ID: {post.id}")
                logging.info(f"  - Post ID: {post.post_id}")
                logging.info(f"  - Original timestamp: {post.original_timestamp}")
                logging.info(f"  - Processing timestamp: {post.timestamp}")
                return post.original_timestamp
            else:
                logging.info(f"No posts found in database for {username}")
            
            # If no posts found, return a very old date to process all posts
            return datetime(2000, 1, 1)
    except Exception as e:
        logging.error(f"Error getting latest post timestamp for {username}: {e}")
        # On error, return a very old date to process all posts
        return datetime(2000, 1, 1)

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
        
        # Get latest processed post timestamp for this user
        latest_timestamp = get_latest_post_timestamp(username)
        logging.info(f"Latest processed post timestamp for {username}: {latest_timestamp}")
        
        # Process casts sequentially to maintain 5-second buffer between API calls
        for cast in casts_response.casts:
            if total_processed[0] >= total_casts_target:
                break
            
            # Only process casts where author username matches the user we're processing
            cast_author_username = cast.author.username if cast.author else None
            if cast_author_username != username:
                logging.debug(f"Skipping cast from different author: {cast_author_username}")
                continue
            
            # Skip if cast is older than or equal to our latest processed post
            try:
                # Convert milliseconds to seconds for timestamp comparison
                cast_timestamp = datetime.fromtimestamp(cast.timestamp / 1000)
                if cast_timestamp <= latest_timestamp:
                    logging.debug(f"Skipping already processed cast from {username} at {cast_timestamp}")
                    continue
            except Exception as e:
                logging.error(f"Error parsing cast timestamp: {e}")
                continue
                
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
    Fetch recent warpcasts and send them to the analyze_social_post endpoint
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
    
    # Get list of users that PRIMARY_USER is following
    following_usernames = await get_following_usernames(client)
    if not following_usernames:
        logging.error("No users to process")
        return
    
    # Set parameters based on test mode
    total_casts_target = 3 if test_mode else len(following_usernames) * 10
    
    # Use lists to allow modification in nested functions
    total_processed = [0]
    total_opportunities = [0]
    
    env = "dev" if not os.environ.get("REPLIT_DEPLOYMENT") else "prod"
    logging.info(f"Running in {env} environment")
    logging.info(f"Target number of casts to process: {total_casts_target}")
    
    async with aiohttp.ClientSession() as session:
        # Process users sequentially to maintain 5-second buffer between API calls
        for username in following_usernames:
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
    try:
        # Run the async function
        asyncio.run(scout_warpcasts(test_mode=args.test))
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
