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

def sync_prod_tables():
    """Synchronize prod tables with dev tables"""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        # First create chain enum type if it doesn't exist
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

        # Drop existing prod tables
        print("Dropping existing prod tables...")
        cur.execute("""
            DROP TABLE IF EXISTS prod_token_opportunities CASCADE;
            DROP TABLE IF EXISTS prod_alpha_reports CASCADE;
            DROP TABLE IF EXISTS prod_social_media_posts CASCADE;
            DROP TABLE IF EXISTS prod_token_reports CASCADE;
        """)
        
        # Create prod tables by copying dev table structures
        print("Creating prod_alpha_reports table...")
        cur.execute("""
            CREATE TABLE prod_alpha_reports (LIKE dev_alpha_reports INCLUDING ALL);
        """)
        
        print("Creating prod_token_opportunities table...")
        cur.execute("""
            CREATE TABLE prod_token_opportunities (LIKE dev_token_opportunities INCLUDING ALL);
        """)
        
        print("Creating prod_social_media_posts table...")
        cur.execute("""
            CREATE TABLE prod_social_media_posts (LIKE dev_social_media_posts INCLUDING ALL);
        """)
        
        print("Creating prod_token_reports table...")
        cur.execute("""
            CREATE TABLE prod_token_reports (LIKE dev_token_reports INCLUDING ALL);
        """)
        
        # Recreate foreign key relationships
        print("Adding foreign key relationships...")
        
        # Token opportunities -> Alpha reports
        cur.execute("""
            ALTER TABLE prod_token_opportunities 
            ADD CONSTRAINT fk_prod_token_opportunities_report 
            FOREIGN KEY (report_id) 
            REFERENCES prod_alpha_reports(id);
        """)
        
        # Social media posts -> Token reports
        cur.execute("""
            ALTER TABLE prod_social_media_posts 
            ADD CONSTRAINT fk_prod_social_media_posts_token_report 
            FOREIGN KEY (token_report_id) 
            REFERENCES prod_token_reports(id);
        """)
        
        conn.commit()
        print("All prod tables have been synchronized with dev tables successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error synchronizing tables: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Synchronizing prod tables with dev tables...")
    sync_prod_tables()
    print("\nChecking triggers...")
    check_triggers()
