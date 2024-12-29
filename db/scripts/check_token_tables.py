from database import get_session
from db.models.alpha import TokenOpportunityDB
from db.models.token import TokenDB

def check_tables():
    """Check current state of token and token_opportunities tables"""
    with get_session() as session:
        # Check token opportunities
        total_opps = session.query(TokenOpportunityDB).count()
        null_token_id_opps = session.query(TokenOpportunityDB).filter(
            TokenOpportunityDB.token_id.is_(None)
        ).count()
        with_contract_opps = session.query(TokenOpportunityDB).filter(
            TokenOpportunityDB.contract_address.isnot(None)
        ).count()
        
        print("\nToken Opportunities Table:")
        print(f"Total records: {total_opps}")
        print(f"Records with null token_id: {null_token_id_opps}")
        print(f"Records with contract_address: {with_contract_opps}")
        
        # Check tokens
        total_tokens = session.query(TokenDB).count()
        with_address_tokens = session.query(TokenDB).filter(
            TokenDB.address.isnot(None)
        ).count()
        
        print("\nTokens Table:")
        print(f"Total records: {total_tokens}")
        print(f"Records with address: {with_address_tokens}")
        
        # Sample some records with relationship info
        print("\nSample Token Opportunities with Token Info (up to 5):")
        samples = session.query(TokenOpportunityDB).filter(
            TokenOpportunityDB.contract_address.isnot(None)
        ).limit(5).all()
        for opp in samples:
            token = session.query(TokenDB).filter(
                TokenDB.chain == opp.chain,
                TokenDB.address.ilike(opp.contract_address) if opp.contract_address else None
            ).first()
            
            print(f"\nOpportunity ID: {opp.id}")
            print(f"Chain: {opp.chain}")
            print(f"Contract Address: {opp.contract_address}")
            print(f"Token ID: {opp.token_id}")
            if token:
                print(f"Matching Token Found - ID: {token.id}, Symbol: {token.symbol}")
            else:
                print("No Matching Token Found")
                # Check for case-insensitive matches that might have been missed
                if opp.contract_address:
                    case_check = session.query(TokenDB).filter(
                        TokenDB.chain == opp.chain,
                        TokenDB.address.isnot(None)
                    ).all()
                    for t in case_check:
                        if t.address and t.address.lower() == opp.contract_address.lower():
                            print(f"Found case-insensitive match! Token ID: {t.id}, Address: {t.address}")

if __name__ == "__main__":
    check_tables()
