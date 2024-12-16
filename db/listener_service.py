import os
import json
import select
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return database_url

def get_api_key():
    """Get API key from environment"""
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")
    return api_key

def notify_alpha_scout(payload):
    """Send notification to alpha scout endpoint"""
    api_key = get_api_key()
    headers = {
        'Content-Type': 'application/json',
        'x-key': api_key
    }
    
    # Get the base URL from environment or use default
    base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    url = f"{base_url}/api/multi_agent_alpha_scout"
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully notified alpha scout for token {payload.get('token_symbol')}")
    except requests.exceptions.RequestException as e:
        print(f"Error notifying alpha scout: {str(e)}")

def main():
    """Main listener function"""
    database_url = get_database_url()
    
    # Connect to database
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Create cursor and listen for notifications
    cur = conn.cursor()
    cur.execute("LISTEN token_report_created;")
    
    print("Listening for token report notifications...")
    
    while True:
        if select.select([conn], [], [], 5) == ([], [], []):
            # Timeout, do nothing
            continue
        
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            try:
                # Parse notification payload
                payload = json.loads(notify.payload)
                print(f"Received notification for token {payload.get('token_symbol')}")
                
                # Forward to alpha scout
                notify_alpha_scout(payload)
            except json.JSONDecodeError as e:
                print(f"Error decoding notification payload: {str(e)}")
            except Exception as e:
                print(f"Error processing notification: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down listener service...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
