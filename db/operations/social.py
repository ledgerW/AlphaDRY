from typing import Dict, Any, Optional
from sqlalchemy.exc import IntegrityError
from ..models.base import get_session
from ..models.social import SocialMediaPostDB, TokenReportDB

def create_social_media_post(post_data: Dict[str, Any], existing_session=None) -> Optional[SocialMediaPostDB]:
    """Create a new social media post entry."""
    if existing_session:
        session = existing_session
        manage_session = False
    else:
        session = get_session()
        manage_session = True
        
    if manage_session:
        session.__enter__()
        
    try:
        # Check if post already exists
        existing = session.query(SocialMediaPostDB).filter(
            SocialMediaPostDB.post_id == post_data['post_id']
        ).first()
        
        if existing:
            return existing
            
        post = SocialMediaPostDB(**post_data)
        session.add(post)
        session.commit()
        session.refresh(post)
        return post
    except IntegrityError:
        if manage_session:
            session.rollback()
        # If we hit a race condition where the post was created between our check and insert
        return session.query(SocialMediaPostDB).filter(
            SocialMediaPostDB.post_id == post_data['post_id']
        ).first()
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating social media post: {e}")
        return None
    finally:
        if manage_session:
            session.__exit__(None, None, None)

def create_token_report(report_data: Dict[str, Any], post_id: Optional[int] = None, existing_session=None) -> Optional[TokenReportDB]:
    """Create a new token report with optional association to a social media post."""
    if existing_session:
        session = existing_session
        manage_session = False
    else:
        session = get_session()
        manage_session = True
        
    if manage_session:
        session.__enter__()
        
    try:
        # Create token report with explicit field mapping
        report = TokenReportDB(
            mentions_purchasable_token=report_data.get('mentions_purchasable_token', False),
            token_symbol=report_data.get('token_symbol'),
            token_chain=report_data.get('token_chain'),
            token_address=report_data.get('token_address'),
            is_listed_on_dex=report_data.get('is_listed_on_dex'),
            trading_pairs=report_data.get('trading_pairs', []),
            confidence_score=report_data.get('confidence_score', 0),
            reasoning=report_data.get('reasoning', '')
        )
        
        # If post_id provided, establish bidirectional relationship
        if post_id:
            post = session.get(SocialMediaPostDB, post_id)
            if post:
                report.social_media_post = post
                post.token_report = report
            else:
                print(f"Warning: SocialMediaPost with ID {post_id} not found")
        
        # Initialize empty opportunities list
        report.opportunities = []
        
        session.add(report)
        session.commit()
        session.refresh(report)
        return report
    except Exception as e:
        if manage_session:
            session.rollback()
        print(f"Error creating token report: {e}")
        return None
    finally:
        if manage_session:
            session.__exit__(None, None, None)
