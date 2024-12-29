import os
import argparse
import csv
from datetime import datetime
from farcaster import Warpcast
from dotenv import load_dotenv
from database import create_db_and_tables, create_warpcast
from schemas import Warpcast as WarpcastSchema
import sys

# Load environment variables
load_dotenv()


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


def setup_environment(env: str):
    """Set up the environment (dev/prod)"""
    if env.lower() == "prod":
        os.environ["REPLIT_DEPLOYMENT"] = "1"
    else:
        os.environ["REPLIT_DEPLOYMENT"] = "0"

def save_to_csv(casts, filename=None):
    """Save warpcasts to a CSV file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"warpcasts_{timestamp}.csv"
    
    fieldnames = [
        'hash', 'thread_hash', 'parent_hash', 'text', 'timestamp',
        'author_fid', 'author_username', 'author_display_name',
        'author_followers', 'author_following',
        'reactions_count', 'replies_count', 'recasts_count',
        'watches_count', 'mentions', 'is_recast', 'pulled_from_user'
    ]
    
    processed_casts = []
    for cast in casts:
        # Handle mentions - check if it's a list of dicts or already processed
        if isinstance(cast.get('mentions', []), list):
            # Filter out None values and ensure all mentions are strings
            mentions = [
                str(mention.get('username', '')) 
                for mention in cast.get('mentions', []) 
                if mention and mention.get('username') is not None
            ]
        else:
            mentions = []

        # Handle nested objects vs flat structure
        reactions = cast.get('reactions', {})
        reactions_count = reactions.get('count', 0) if isinstance(reactions, dict) else reactions

        replies = cast.get('replies', {})
        replies_count = replies.get('count', 0) if isinstance(replies, dict) else replies

        recasts = cast.get('recasts', {})
        recasts_count = recasts.get('count', 0) if isinstance(recasts, dict) else recasts

        watches = cast.get('watches', {})
        watches_count = watches.get('count', 0) if isinstance(watches, dict) else watches

        # Handle author information - could be nested or flat
        author = cast.get('author', {})
        if isinstance(author, dict):
            author_fid = author.get('fid', '')
            author_username = author.get('username', '')
            author_display_name = author.get('display_name', '')
            author_followers = author.get('follower_count', 0)
            author_following = author.get('following_count', 0)
        else:
            author_fid = cast.get('author_fid', '')
            author_username = cast.get('username', '')
            author_display_name = cast.get('display_name', '')
            author_followers = cast.get('follower_count', 0)
            author_following = cast.get('following_count', 0)
        
        processed_cast = {
            'hash': cast.get('hash', ''),
            'thread_hash': cast.get('thread_hash', ''),
            'parent_hash': cast.get('parent_hash', ''),
            'text': cast.get('text', ''),
            'timestamp': cast.get('timestamp', ''),
            'author_fid': author_fid,
            'author_username': author_username,
            'author_display_name': author_display_name,
            'author_followers': author_followers,
            'author_following': author_following,
            'reactions_count': reactions_count,
            'replies_count': replies_count,
            'recasts_count': recasts_count,
            'watches_count': watches_count,
            'mentions': ','.join(filter(None, mentions)),  # Additional filter for safety
            'is_recast': cast.get('recast', False),
            'pulled_from_user': cast.get('pulled_from_user', '')
        }
        processed_casts.append(processed_cast)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_casts)
    
    return filename

def load_warpcasts(env: str, num_users: int, casts_per_user: int, output_type: str, csv_filename: str = None):
    """Load warpcasts into the database or CSV file"""
    # Set up environment
    setup_environment(env)
    
    # Initialize database if saving to db
    if output_type == 'db':
        create_db_and_tables()
    
    # Initialize Warpcast client
    mnemonic = os.environ.get("MNEMONIC_ENV_VAR")
    if not mnemonic:
        print("Error: MNEMONIC_ENV_VAR environment variable not set")
        sys.exit(1)
    
    client = Warpcast(mnemonic=mnemonic)
    
    # Test API connection
    try:
        client.get_healthcheck()
    except Exception as e:
        print(f"Error connecting to Warpcast API: {e}")
        sys.exit(1)
    
    selected_usernames = USERNAMES[:num_users]
    total_casts_loaded = 0
    all_casts = []  # Store casts if saving to CSV
    
    print(f"\nFetching {casts_per_user} casts for each of {len(selected_usernames)} users...")
    
    for username in selected_usernames:
        try:
            print(f"\nProcessing user: {username}")
            
            user = client.get_user_by_username(username)
            if not user:
                print(f"Could not find user: {username}")
                continue
            
            casts_response = client.get_casts(user.fid, limit=casts_per_user)
            if not casts_response or not casts_response.casts:
                print(f"No casts found for user: {username}")
                continue
            
            user_casts_loaded = 0
            for cast in casts_response.casts:
                try:
                    warpcast = WarpcastSchema.from_cast(cast.dict())
                    if output_type == 'db':
                        result = create_warpcast(warpcast, username)
                        if result:
                            user_casts_loaded += 1
                            total_casts_loaded += 1
                    else:  # CSV
                        cast_dict = cast.dict()  # Get the raw cast data
                        cast_dict['pulled_from_user'] = username  # Add the username we're currently processing
                        all_casts.append(cast_dict)
                        user_casts_loaded += 1
                        total_casts_loaded += 1
                except Exception as e:
                    print(f"Error processing cast: {e}")
                    continue
            
            print(f"Processed {user_casts_loaded} casts for {username}")
            
        except Exception as e:
            print(f"Error processing user {username}: {e}")
            continue
    
    if output_type == 'csv' and all_casts:
        saved_filename = save_to_csv(all_casts, csv_filename)
        print(f"\nSaved {total_casts_loaded} casts to {saved_filename}")
    else:
        print(f"\nFinished! Total casts loaded to database: {total_casts_loaded}")

def main():
    parser = argparse.ArgumentParser(description='Load Warpcasts into database or CSV')
    parser.add_argument('--env', type=str, choices=['dev', 'prod'], default='dev',
                      help='Environment to load casts into (dev/prod)')
    parser.add_argument('--users', type=int, default=5,
                      help='Number of users to load casts for')
    parser.add_argument('--casts', type=int, default=10,
                      help='Number of casts to load per user')
    parser.add_argument('--output', type=str, choices=['db', 'csv'], default='db',
                      help='Output type: database or CSV file')
    parser.add_argument('--filename', type=str, default=None,
                      help='Optional CSV filename (only used if output=csv)')
    
    args = parser.parse_args()
    
    load_warpcasts(args.env, args.users, args.casts, args.output, args.filename)

if __name__ == "__main__":
    main()
