import os
import argparse
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

def load_warpcasts(env: str, num_users: int, casts_per_user: int):
    """Load warpcasts into the database"""
    # Set up environment
    setup_environment(env)
    
    # Initialize database
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
    
    # Limit number of users based on input
    selected_usernames = USERNAMES[:num_users]
    
    total_casts_loaded = 0
    
    print(f"\nLoading {casts_per_user} casts for each of {len(selected_usernames)} users in {env} environment...")
    
    for username in selected_usernames:
        try:
            print(f"\nProcessing user: {username}")
            
            # Get user FID
            user = client.get_user_by_username(username)
            if not user:
                print(f"Could not find user: {username}")
                continue
            
            # Get casts for user
            casts_response = client.get_casts(user.fid, limit=casts_per_user)
            if not casts_response or not casts_response.casts:
                print(f"No casts found for user: {username}")
                continue
            
            # Store casts in database
            user_casts_loaded = 0
            for cast in casts_response.casts:
                try:
                    warpcast = WarpcastSchema.from_cast(cast.dict())
                    result = create_warpcast(warpcast, username)  # Pass the username here
                    if result:
                        user_casts_loaded += 1
                        total_casts_loaded += 1
                except Exception as e:
                    print(f"Error processing cast: {e}")
                    continue
            
            print(f"Loaded {user_casts_loaded} casts for {username}")
            
        except Exception as e:
            print(f"Error processing user {username}: {e}")
            continue
    
    print(f"\nFinished! Total casts loaded: {total_casts_loaded}")

def main():
    parser = argparse.ArgumentParser(description='Load Warpcasts into database')
    parser.add_argument('--env', type=str, choices=['dev', 'prod'], default='dev',
                      help='Environment to load casts into (dev/prod)')
    parser.add_argument('--users', type=int, default=5,
                      help='Number of users to load casts for')
    parser.add_argument('--casts', type=int, default=10,
                      help='Number of casts to load per user')
    
    args = parser.parse_args()
    
    load_warpcasts(args.env, args.users, args.casts)

if __name__ == "__main__":
    main()
