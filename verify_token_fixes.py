from database import get_session
from sqlalchemy import text

def verify_fixes():
    """Verify the token address fixes"""
    with get_session() as session:
        # Check for any duplicate addresses (case-insensitive for Base)
        result = session.execute(text("""
            WITH token_groups AS (
                SELECT chain,
                       CASE 
                           WHEN address LIKE '0x%' THEN LOWER(address)
                           ELSE address
                       END as normalized_address,
                       COUNT(*) as count,
                       array_agg(id) as token_ids,
                       array_agg(address) as addresses
                FROM prod_tokens
                WHERE address IS NOT NULL
                GROUP BY chain,
                         CASE 
                             WHEN address LIKE '0x%' THEN LOWER(address)
                             ELSE address
                         END
                HAVING COUNT(*) > 1
            )
            SELECT * FROM token_groups;
        """)).fetchall()
        
        if result:
            print("\nFound duplicate addresses:")
            for row in result:
                print(f"Chain: {row.chain}")
                print(f"Normalized Address: {row.normalized_address}")
                print(f"Count: {row.count}")
                print(f"Token IDs: {row.token_ids}")
                print(f"Addresses: {row.addresses}\n")
        else:
            print("\nNo duplicate addresses found!")
        
        # Check Base token addresses are lowercase
        result = session.execute(text("""
            SELECT id, chain, address
            FROM prod_tokens
            WHERE address LIKE '0x%'
            AND address != LOWER(address);
        """)).fetchall()
        
        if result:
            print("\nFound Base addresses not in lowercase:")
            for row in result:
                print(f"ID: {row.id}, Chain: {row.chain}, Address: {row.address}")
        else:
            print("\nAll Base addresses are lowercase!")
        
        # Check for orphaned relationships
        result = session.execute(text("""
            SELECT 'token_opportunities' as table_name,
                   COUNT(*) as count
            FROM prod_token_opportunities
            WHERE token_id IS NULL
            AND contract_address IS NOT NULL
            UNION ALL
            SELECT 'token_reports' as table_name,
                   COUNT(*) as count
            FROM prod_token_reports
            WHERE token_id IS NULL
            AND token_address IS NOT NULL;
        """)).fetchall()
        
        print("\nOrphaned relationships:")
        for row in result:
            print(f"{row.table_name}: {row.count}")

if __name__ == "__main__":
    verify_fixes()
