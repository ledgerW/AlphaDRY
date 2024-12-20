from typing import Dict, Any, List, Optional
from ..models.base import get_session
from ..models.alpha import AlphaReportDB, TokenOpportunityDB
from ..models.social import TokenReportDB
from agents.models import Chain
import time

def create_alpha_report(report_data: Dict[str, Any]) -> Optional[AlphaReportDB]:
    """Create a new alpha report with its associated token opportunities."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            with get_session() as session:
                # Create the report
                report = AlphaReportDB(
                    is_relevant=report_data["is_relevant"],
                    analysis=report_data["analysis"],
                    message=report_data.get("message", "")
                )
                session.add(report)
                session.flush()  # Flush to get the report ID

                # If token_report_id is provided, fetch the token report
                token_report = None
                if "token_report_id" in report_data:
                    token_report = session.get(TokenReportDB, report_data["token_report_id"])
                    if not token_report:
                        print(f"Warning: TokenReport with ID {report_data['token_report_id']} not found")
                        continue

                # Create associated opportunities
                for opp_data in report_data["opportunities"]:
                    # Handle chain conversion
                    chain_value = opp_data.get('chain')
                    
                    if isinstance(chain_value, str):
                        # Convert string to Chain enum using case-insensitive matching
                        chain_lower = chain_value.lower()
                        
                        try:
                            # Find matching enum by value (case-insensitive)
                            chain_enum = None
                            for enum_val in Chain:
                                if enum_val.value == chain_lower:
                                    chain_enum = enum_val
                                    break
                            
                            if chain_enum is None:
                                print(f"Warning: Invalid chain value '{chain_value}', defaulting to ethereum")
                                chain_enum = Chain.ETHEREUM
                            
                            opp_data['chain'] = chain_enum
                        except Exception as e:
                            print(f"Warning: Error converting chain '{chain_value}', defaulting to ethereum")
                            opp_data['chain'] = Chain.ETHEREUM
                    
                    
                    # Create opportunity with both relationships
                    opportunity = TokenOpportunityDB(
                        name=opp_data.get('name'),
                        chain=opp_data.get('chain'),
                        contract_address=opp_data.get('contract_address'),
                        market_cap=opp_data.get('market_cap'),
                        community_score=opp_data.get('community_score'),
                        safety_score=opp_data.get('safety_score'),
                        justification=opp_data.get('justification'),
                        sources=opp_data.get('sources', []),
                        recommendation=opp_data.get('recommendation', 'Hold'),
                        report_id=report.id,  # Set alpha report relationship
                        token_report_id=report_data.get("token_report_id")  # Set token report relationship
                    )
                    
                    # Establish bidirectional relationships
                    opportunity.report = report
                    report.opportunities.append(opportunity)
                    
                    if token_report:
                        opportunity.token_report = token_report
                        token_report.opportunities.append(opportunity)
                    
                    session.add(opportunity)

                session.commit()
                session.refresh(report)
                return report
                
        except Exception as e:
            session.rollback()
            print(f"Error creating alpha report (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None

def get_alpha_report(report_id: int) -> Optional[AlphaReportDB]:
    """Get an alpha report by ID."""
    with get_session() as session:
        return session.get(AlphaReportDB, report_id)

def get_all_alpha_reports() -> List[AlphaReportDB]:
    """Get all alpha reports."""
    with get_session() as session:
        return session.query(AlphaReportDB).all()
