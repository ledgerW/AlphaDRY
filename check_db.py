import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def verify_and_fix_database():
    """Verify and fix database configuration for production environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # 1. Set deployment environment
        print("Setting deployment environment...")
        cur.execute("SELECT current_setting('app.deployment_env', TRUE)")
        current_env = cur.fetchone()[0]
        
        if os.getenv("REPLIT_DEPLOYMENT") == "1":
            if current_env != 'production':
                cur.execute("SELECT set_config('app.deployment_env', 'production', FALSE)")
                print("Set app.deployment_env to 'production'")
        
        # 2. Verify table exists
        print("Verifying table existence...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'prod_token_reports'
            )
        """)
        table_exists = cur.fetchone()[0]
        if not table_exists:
            raise Exception("prod_token_reports table does not exist")
        
        # 3. Verify trigger function
        print("Verifying trigger function...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_proc 
                WHERE proname = 'notify_alpha_scout'
            )
        """)
        function_exists = cur.fetchone()[0]
        if not function_exists:
            print("Trigger function does not exist, creating...")
            with open('db/deployment_safety.sql', 'r') as f:
                cur.execute(f.read())
        
        # 4. Verify trigger on correct table
        print("Verifying trigger...")
        cur.execute("""
            SELECT tgname 
            FROM pg_trigger 
            WHERE tgrelid = 'prod_token_reports'::regclass 
            AND tgname = 'token_report_created'
        """)
        trigger_exists = cur.fetchone() is not None
        
        if not trigger_exists:
            print("Trigger not found on prod_token_reports, recreating...")
            # Drop any existing trigger
            cur.execute("DROP TRIGGER IF EXISTS token_report_created ON prod_token_reports")
            # Create new trigger
            cur.execute("""
                CREATE TRIGGER token_report_created
                AFTER INSERT ON prod_token_reports
                FOR EACH ROW
                EXECUTE FUNCTION notify_alpha_scout()
            """)
        
        # 5. Test notification system
        print("Testing notification system...")
        cur.execute("LISTEN token_report_created")
        cur.execute("""
            INSERT INTO prod_token_reports (
                mentions_purchasable_token,
                token_symbol,
                token_chain,
                token_address,
                is_listed_on_dex,
                trading_pairs,
                confidence_score,
                reasoning
            ) VALUES (
                true,
                'TEST',
                'ethereum',
                '0xtest',
                true,
                ARRAY['TEST/ETH'],
                9,
                'Configuration test'
            )
        """)
        
        conn.poll()
        if conn.notifies:
            notify = conn.notifies.pop()
            print(f"✓ Notification system working: {notify.payload}")
        else:
            print("⚠ Warning: No notification received from test insert")
        
        print("\n✓ Database configuration verified and fixed where necessary")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verify_and_fix_database()
