from typing import Dict, Any, Optional
from sqlalchemy.exc import IntegrityError
from ..models.base import get_session
from ..models.social import SocialMediaPostDB, TokenReportDB

def create_social_media_post(post_data: Dict[str, Any]) -> Optional[SocialMediaPostDB]:
    """Create a new social media post entry."""
    with get_session() as session:
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
            session.rollback()
            # If we hit a race condition where the post was created between our check and insert
            return session.query(SocialMediaPostDB).filter(
                SocialMediaPostDB.post_id == post_data['post_id']
            ).first()
        except Exception as e:
            session.rollback()
            print(f"Error creating social media post: {e}")
            return None

def create_token_report(report_data: Dict[str, Any], post_id: Optional[int] = None) -> Optional[TokenReportDB]:
    """Create a new token report with optional association to a social media post."""
    with get_session() as session:
        try:
            report = TokenReportDB(**report_data)
            if post_id:
                post = session.get(SocialMediaPostDB, post_id)
                if post:
                    post.token_report = report
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        except Exception as e:
            session.rollback()
            print(f"Error creating token report: {e}")
            return None
