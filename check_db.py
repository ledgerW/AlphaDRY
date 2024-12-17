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

def update_token_opportunities_table():
    """Add chain column to prod_token_opportunities table"""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        # First check if the chain type exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_type 
                WHERE typname = 'chain'
            );
        """)
        chain_type_exists = cur.fetchone()[0]
        
        if not chain_type_exists:
            print("Creating chain enum type...")
            cur.execute("""
                CREATE TYPE chain AS ENUM ('BASE', 'SOLANA');
            """)
            print("Chain enum type created successfully")
        
        # Check if chain column exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'prod_token_opportunities' 
                AND column_name = 'chain'
            );
        """)
        chain_column_exists = cur.fetchone()[0]
        
        if not chain_column_exists:
            print("Adding chain column to prod_token_opportunities...")
            # Add the chain column
            cur.execute("""
                ALTER TABLE prod_token_opportunities 
                ADD COLUMN chain chain NOT NULL DEFAULT 'BASE';
            """)
            print("Chain column added successfully")
        else:
            print("Chain column already exists")
        
        conn.commit()
        print("Database update completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating database: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Updating token opportunities table...")
    update_token_opportunities_table()
    print("\nChecking triggers...")
    check_triggers()
