from database import get_session
from sqlalchemy import text

def check_token_data():
    """Check token data in both prod tables"""
    with get_session() as session:
        # Get all tokens with addresses
        tokens = session.execute(text("""
            SELECT id, chain, symbol, address 
            FROM prod_tokens 
            WHERE address IS NOT NULL
            ORDER BY id
        """)).fetchall()
        
        print("\nProd Tokens Table Data:")
        for token in tokens:
            print(f"ID: {token.id}, Chain: {token.chain}, "
                  f"Symbol: {token.symbol}, Address: {token.address}")
        
        # Get all opportunities with contract addresses
        opportunities = session.execute(text("""
            SELECT id, chain, token_id, contract_address 
            FROM prod_token_opportunities 
            WHERE contract_address IS NOT NULL
            ORDER BY id
        """)).fetchall()
        
        print("\nProd Token Opportunities Table Data:")
        for opp in opportunities:
            print(f"ID: {opp.id}, Chain: {opp.chain}, "
                  f"Token ID: {opp.token_id}, Contract: {opp.contract_address}")
            
            # If opportunity has a token_id, verify the token exists and show its data
            if opp.token_id:
                token = session.execute(text("""
                    SELECT id, chain, symbol, address 
                    FROM prod_tokens 
                    WHERE id = :token_id
                """), {'token_id': opp.token_id}).first()
                
                if token:
                    print(f"  -> Linked Token: ID: {token.id}, Chain: {token.chain}, "
                          f"Symbol: {token.symbol}, Address: {token.address}")
                else:
                    print(f"  -> WARNING: Token ID {opp.token_id} not found in prod_tokens!")

if __name__ == "__main__":
    check_token_data()
