from sqlalchemy import text, Column, String, JSON, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import get_session
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from agents.models import Chain

# Define production-specific models
class ProdTokenDB(SQLModel, table=True):
    """Production database model for tokens"""
    __tablename__ = "prod_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    name: str
    chain: Chain = Field(sa_column=Column(String, nullable=False))
    address: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    token_opportunities: List["ProdTokenOpportunityDB"] = Relationship(back_populates="token")

class ProdTokenOpportunityDB(SQLModel, table=True):
    """Production database model for token opportunities"""
    __tablename__ = "prod_token_opportunities"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    chain: Chain = Field(sa_column=Column(String, nullable=False))
    contract_address: Optional[str]
    market_cap: Optional[float]
    community_score: int
    safety_score: int
    justification: str
    sources: List[str] = Field(sa_column=Column(JSON))
    recommendation: str = Field(default="Hold")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    report_id: Optional[int] = Field(default=None)
    token_report_id: Optional[int] = Field(default=None)
    
    token_id: Optional[int] = Field(default=None, foreign_key="prod_tokens.id")
    token: Optional[ProdTokenDB] = Relationship(back_populates="token_opportunities")

def update_token_relationships():
    """Update token_id values in prod_token_opportunities table based on contract address matches"""
    with get_session() as session:
        # Get all opportunities with non-null contract_address (including those that might have wrong token_id)
        opportunities = session.query(ProdTokenOpportunityDB).filter(
            ProdTokenOpportunityDB.contract_address.isnot(None)
        ).all()
        
        print(f"Found {len(opportunities)} opportunities to process")
        
        updates = 0
        for opp in opportunities:
            # Find matching token by chain and contract address (case insensitive)
            matching_token = session.query(ProdTokenDB).filter(
                ProdTokenDB.chain == opp.chain,
                func.lower(ProdTokenDB.address) == func.lower(opp.contract_address)
            ).first()
            
            if matching_token:
                if opp.token_id != matching_token.id:
                    opp.token_id = matching_token.id
                    updates += 1
                    print(f"Matched opportunity {opp.id} with token {matching_token.id} "
                          f"(chain: {opp.chain}, contract: {opp.contract_address})")
            else:
                # If no match found and opportunity has a token_id, clear it
                if opp.token_id is not None:
                    print(f"Clearing invalid token_id {opp.token_id} from opportunity {opp.id} "
                          f"(chain: {opp.chain}, contract: {opp.contract_address})")
                    opp.token_id = None
                    updates += 1
        
        if updates > 0:
            session.commit()
            print(f"\nSuccessfully updated {updates} token opportunities")
        else:
            print("\nNo matches found to update")

        # Print final stats
        total = session.query(ProdTokenOpportunityDB).count()
        with_token = session.query(ProdTokenOpportunityDB).filter(
            ProdTokenOpportunityDB.token_id.isnot(None)
        ).count()
        with_contract = session.query(ProdTokenOpportunityDB).filter(
            ProdTokenOpportunityDB.contract_address.isnot(None)
        ).count()
        
        print(f"\nFinal Statistics:")
        print(f"Total opportunities: {total}")
        print(f"Opportunities with token_id: {with_token}")
        print(f"Opportunities with contract_address: {with_contract}")
        print(f"Opportunities missing token_id: {total - with_token}")

if __name__ == "__main__":
    update_token_relationships()
