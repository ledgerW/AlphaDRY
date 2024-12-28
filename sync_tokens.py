import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

def sync_tokens():
    """
    One-time script to populate prod_tokens table from existing prod_token_reports entries
    and update prod_token_reports entries with the corresponding token_ids
    """
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Create database engine
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Start transaction
            with conn.begin():
                # First handle tokens with addresses
                logging.info("Processing tokens with addresses...")
                address_tokens = conn.execute(text("""
                    SELECT DISTINCT
                        token_chain as chain,
                        token_symbol as symbol,
                        token_address as address
                    FROM prod_token_reports
                    WHERE token_chain IS NOT NULL
                    AND token_address IS NOT NULL
                    AND mentions_purchasable_token = true
                """)).fetchall()

                logging.info(f"Found {len(address_tokens)} tokens with addresses")

                # Process tokens with addresses
                for token in address_tokens:
                    # Check if token already exists by address (case-insensitive)
                    existing = conn.execute(text("""
                        SELECT id
                        FROM prod_tokens
                        WHERE chain = :chain
                        AND LOWER(address) = LOWER(:address)
                    """), {
                        'chain': token.chain,
                        'address': token.address
                    }).first()

                    if existing:
                        token_id = existing.id
                        logging.info(f"Token already exists: {token.symbol} ({token.chain})")
                    else:
                        # Create new token entry with timestamp
                        result = conn.execute(text("""
                            INSERT INTO prod_tokens (symbol, name, chain, address, created_at)
                            VALUES (:symbol, :symbol, :chain, :address, NOW())
                            ON CONFLICT (chain, address) DO UPDATE 
                            SET symbol = EXCLUDED.symbol, 
                                name = EXCLUDED.symbol
                            RETURNING id
                        """), {
                            'symbol': token.symbol,
                            'chain': token.chain,
                            'address': token.address
                        })
                        token_id = result.scalar()
                        logging.info(f"Created new token: {token.symbol} ({token.chain})")

                    # Update token_reports with token_id (case-insensitive address matching)
                    conn.execute(text("""
                        UPDATE prod_token_reports
                        SET token_id = :token_id
                        WHERE token_chain = :chain
                        AND LOWER(token_address) = LOWER(:address)
                        AND (token_id IS NULL OR token_id != :token_id)
                    """), {
                        'token_id': token_id,
                        'chain': token.chain,
                        'address': token.address
                    })

                # Then try to match remaining token reports without addresses to existing tokens that have addresses
                logging.info("\nProcessing remaining token reports without addresses...")
                
                # Update token reports by matching on symbol and chain with tokens that have addresses
                matched = conn.execute(text("""
                    UPDATE prod_token_reports tr
                    SET token_id = t.id
                    FROM prod_tokens t
                    WHERE tr.token_chain = t.chain
                    AND tr.token_symbol = t.symbol
                    AND t.address IS NOT NULL
                    AND tr.token_address IS NULL
                    AND tr.token_id IS NULL
                    AND tr.mentions_purchasable_token = true
                    RETURNING tr.token_symbol, tr.token_chain, t.id
                """)).fetchall()

                logging.info(f"Matched {len(matched)} token reports to existing tokens by symbol and chain")
                for match in matched:
                    logging.info(f"Matched token report to existing token: {match.token_symbol} ({match.token_chain})")

                # Log final counts
                token_count = conn.execute(text("SELECT COUNT(*) FROM prod_tokens")).scalar()
                report_count = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM prod_token_reports
                    WHERE token_id IS NOT NULL
                """)).scalar()
                
                # Get counts of unlinked purchasable token reports
                unlinked_count = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM prod_token_reports
                    WHERE token_id IS NULL
                    AND mentions_purchasable_token = true
                    AND token_chain IS NOT NULL
                    AND (token_address IS NOT NULL OR token_symbol IS NOT NULL)
                """)).scalar()

                logging.info(f"\nSync complete!")
                logging.info(f"Total tokens in prod_tokens: {token_count}")
                logging.info(f"Total token reports with token_id: {report_count}")
                logging.info(f"Remaining unlinked purchasable token reports: {unlinked_count}")

    except Exception as e:
        logging.error(f"Error syncing tokens: {str(e)}")
        raise

if __name__ == "__main__":
    sync_tokens()
