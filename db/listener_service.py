import os
import json
import select
import time
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

# Maximum number of reconnection attempts
MAX_RETRIES = 5
# Base delay between retries (will be multiplied by retry attempt number)
RETRY_DELAY = 5
# How often to check connection health (seconds)
HEALTH_CHECK_INTERVAL = 60

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
    base_url = os.getenv('API_BASE_URL', 'http://0.0.0.0:8000')
    url = f"{base_url}/api/multi_agent_alpha_scout"
    
    print(f"Sending request to {url} with payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully notified alpha scout for token {payload.get('token_symbol')}")
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error notifying alpha scout: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")

def create_connection():
    """Create a new database connection with retries"""
    database_url = get_database_url()
    retry_count = 0
    last_error = None
    
    while retry_count < MAX_RETRIES:
        try:
            print(f"Attempting database connection (attempt {retry_count + 1}/{MAX_RETRIES})...")
            conn = psycopg2.connect(database_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Create cursor and listen for notifications
            cur = conn.cursor()
            cur.execute("LISTEN token_report_created;")
            
            print("Successfully connected to database")
            return conn
            
        except psycopg2.Error as e:
            last_error = e
            retry_count += 1
            if retry_count < MAX_RETRIES:
                sleep_time = RETRY_DELAY * retry_count
                print(f"Connection failed: {str(e)}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            
    raise Exception(f"Failed to connect after {MAX_RETRIES} attempts. Last error: {str(last_error)}")

def check_connection(conn):
    """Check if the connection is still healthy"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return True
    except (psycopg2.Error, psycopg2.OperationalError):
        return False

def main():
    """Main listener function"""
    print("Starting listener service...")
    print("Debug: Using DATABASE_URL:", os.getenv("DATABASE_URL", "not set"))
    print("Debug: Using API_KEY:", "..." + os.getenv("API_KEY", "not set")[-4:] if os.getenv("API_KEY") else "not set")
    print("Debug: Using API_BASE_URL:", os.getenv("API_BASE_URL", "http://localhost:8000"))
    
    conn = None
    last_health_check = time.time()
    
    while True:
        try:
            # Create initial connection if needed
            if conn is None:
                conn = create_connection()
                continue
            
            # Periodic health check
            current_time = time.time()
            if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
                if not check_connection(conn):
                    print("Connection health check failed. Reconnecting...")
                    conn.close()
                    conn = create_connection()
                last_health_check = current_time
            
            # Wait for notifications with timeout
            if select.select([conn], [], [], 5) == ([], [], []):
                continue
            
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                try:
                    print(f"Debug: Received raw notification: {notify.payload}")
                    
                    # Parse notification payload
                    payload = json.loads(notify.payload)
                    print(f"Debug: Parsed payload: {json.dumps(payload, indent=2)}")
                    print(f"Received notification for token {payload.get('token_symbol')}")
                    
                    # Forward to alpha scout
                    notify_alpha_scout(payload)
                except json.JSONDecodeError as e:
                    print(f"Error decoding notification payload: {str(e)}")
                    print(f"Raw payload was: {notify.payload}")
                except Exception as e:
                    print(f"Error processing notification: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            print(f"Database error occurred: {str(e)}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            conn = None
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            if conn:
                try:
                    conn.close()
                except:
                    pass
            conn = None
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down listener service...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        print(traceback.format_exc())
