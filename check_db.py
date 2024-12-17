import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_triggers():
    """Check if the token report triggers exist in the database"""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        # Query to check triggers
        cur.execute("""
            SELECT 
                event_object_table as table_name,
                trigger_name,
                event_manipulation as trigger_event
            FROM information_schema.triggers
            WHERE event_object_table IN ('dev_token_reports', 'prod_token_reports')
            ORDER BY event_object_table;
        """)
        
        triggers = cur.fetchall()
        print("\nExisting triggers:")
        if not triggers:
            print("No triggers found for token report tables!")
        else:
            for trigger in triggers:
                print(f"Table: {trigger[0]}")
                print(f"Trigger Name: {trigger[1]}")
                print(f"Event: {trigger[2]}")
                print("---")
                
        # Check if notify_alpha_scout function exists
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 
                FROM pg_proc 
                WHERE proname = 'notify_alpha_scout'
            );
        """)
        function_exists = cur.fetchone()[0]
        print(f"\nnotify_alpha_scout function exists: {function_exists}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_triggers()
