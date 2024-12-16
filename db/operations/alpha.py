from typing import Dict, Any, List, Optional
from ..models.base import get_session
from ..models.alpha import AlphaReportDB, TokenOpportunityDB
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

                # Create associated opportunities
                for opp_data in report_data["opportunities"]:
                    # Handle chain conversion
                    chain_value = opp_data.get('chain')
                    if isinstance(chain_value, str):
                        # Try to match the chain value case-insensitively
                        chain_value = chain_value.upper()
                        if chain_value == 'BASE':
                            opp_data['chain'] = Chain.BASE
                        elif chain_value == 'SOLANA':
                            opp_data['chain'] = Chain.SOLANA
                        
                    opportunity = TokenOpportunityDB(
                        report_id=report.id,
                        **opp_data
                    )
                    session.add(opportunity)

                session.commit()
                session.refresh(report)
                return report
                
        except Exception as e:
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
