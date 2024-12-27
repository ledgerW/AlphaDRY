import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

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
            DROP TABLE IF EXISTS prod_tokens CASCADE;
        """)
        
        # Create prod tables by copying dev table structures
        print("Creating prod_tokens table...")
        cur.execute("""
            CREATE TABLE prod_tokens (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                address VARCHAR,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX idx_prod_tokens_symbol ON prod_tokens(symbol);
            CREATE INDEX idx_prod_tokens_address ON prod_tokens(address);
            CREATE UNIQUE INDEX uq_prod_tokens_chain_address ON prod_tokens(chain, address);
        """)

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
        
        # Token opportunities -> Token reports
        cur.execute("""
            ALTER TABLE prod_token_opportunities 
            ADD CONSTRAINT fk_prod_token_opportunities_token_report 
            FOREIGN KEY (token_report_id) 
            REFERENCES prod_token_reports(id)
            ON DELETE SET NULL;
        """)

        # Token opportunities -> Tokens
        cur.execute("""
            ALTER TABLE prod_token_opportunities 
            ADD CONSTRAINT fk_prod_token_opportunities_token 
            FOREIGN KEY (token_id) 
            REFERENCES prod_tokens(id)
            ON DELETE SET NULL;
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
