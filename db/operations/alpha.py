from typing import Dict, Any, List, Optional
from ..models.base import get_session
from ..models.alpha import AlphaReportDB, TokenOpportunityDB
from ..models.social import TokenReportDB
from agents.models import Chain
import time
from datetime import datetime, timedelta
from sqlalchemy import func

def normalize_chain(chain_value: str) -> Chain:
    """Helper function to normalize chain values to Chain enum."""
    if not isinstance(chain_value, str):
        return Chain.ETHEREUM
        
    chain_lower = chain_value.lower()
    
    for enum_val in Chain:
        if enum_val.value == chain_lower:
            return enum_val
            
    print(f"Warning: Invalid chain value '{chain_value}', defaulting to ethereum")
    return Chain.ETHEREUM

def create_alpha_report(report_data: Dict[str, Any], existing_session=None) -> Optional[AlphaReportDB]:
    """Create a new alpha report with its associated token opportunities."""
    session = existing_session or get_session()
    manage_session = not existing_session
    
    if manage_session:
        session.begin()
    
    try:
        # Create the report
        report = AlphaReportDB(
            is_relevant=report_data["is_relevant"],
            analysis=report_data["analysis"],
            message=report_data.get("message", "")
        )
        session.add(report)
        
        # Get token report if ID provided
        token_report = None
        if "token_report_id" in report_data:
            token_report = session.get(TokenReportDB, report_data["token_report_id"])
            if not token_report:
                print(f"Warning: TokenReport with ID {report_data['token_report_id']} not found")
        
        # Create opportunities
        for opp_data in report_data["opportunities"]:
            opportunity = TokenOpportunityDB(
                name=opp_data.get('name'),
                chain=normalize_chain(opp_data.get('chain')),
                contract_address=opp_data.get('contract_address'),
                market_cap=opp_data.get('market_cap'),
                community_score=opp_data.get('community_score'),
                safety_score=opp_data.get('safety_score'),
                justification=opp_data.get('justification'),
                sources=opp_data.get('sources', []),
                recommendation=opp_data.get('recommendation', 'Hold')
            )
            
            # Set relationships
            opportunity.report = report
            if token_report:
                opportunity.token_report = token_report
                if token_report.token:
                    opportunity.token = token_report.token
            
            session.add(opportunity)
        
        session.flush()
        
        if manage_session:
            session.commit()
        
        return report
        
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating alpha report: {e}")
        return None
        
    finally:
        if manage_session:
            session.close()

def get_alpha_report(report_id: int) -> Optional[AlphaReportDB]:
    """Get an alpha report by ID."""
    with get_session() as session:
        return session.get(AlphaReportDB, report_id)

def get_all_alpha_reports() -> List[AlphaReportDB]:
    """Get all alpha reports."""
    with get_session() as session:
        return session.query(AlphaReportDB).all()

def has_recent_token_report(contract_address: str, hours: int = 1) -> bool:
    """
    Check if there are multiple token reports for the given contract address within the specified hours.
    Returns True if there is more than one report, indicating alpha_scout has already run.
    
    Args:
        contract_address: The contract address to check
        hours: Number of hours to look back (default: 1)
        
    Returns:
        bool: True if more than one recent report exists (indicating alpha_scout already ran), False otherwise
    """
    if not contract_address:
        return False
        
    with get_session() as session:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Count token reports with matching contract address within the time window
        report_count = session.query(func.count(TokenReportDB.id)).filter(
            TokenReportDB.token_address == contract_address,
            TokenReportDB.created_at >= cutoff_time
        ).scalar()
        
        # Return True if there is more than one report (indicating alpha_scout already ran)
        return report_count > 1
