from typing import Optional, List, Any
from ..models.base import get_session
from ..models.warpcast import get_model
from schemas import Warpcast

def create_warpcast(warpcast: Warpcast, pulled_from_user: str) -> Optional[Any]:
    """
    Create a new warpcast entry if it doesn't exist.
    Returns None if a warpcast with the same hash already exists.
    """
    Model = get_model()
    with get_session() as session:
        try:
            # Check if warpcast already exists
            existing = session.query(Model).filter(Model.hash == warpcast.hash).first()
            
            if existing:
                return None
                
            db_warpcast = Model.from_warpcast(warpcast, pulled_from_user)
            session.add(db_warpcast)
            session.commit()
            session.refresh(db_warpcast)
            return db_warpcast
        except Exception as e:
            session.rollback()
            print(f"Error creating warpcast: {e}")
            return None

def get_warpcast_by_hash(hash: str) -> Optional[Warpcast]:
    """Get a warpcast by its hash."""
    Model = get_model()
    with get_session() as session:
        db_warpcast = session.query(Model).filter(Model.hash == hash).first()
        return db_warpcast.to_warpcast() if db_warpcast else None

def get_warpcasts_by_username(username: str) -> List[Warpcast]:
    """Get all warpcasts by a specific username."""
    Model = get_model()
    with get_session() as session:
        db_warpcasts = session.query(Model).filter(Model.username == username).all()
        return [cast.to_warpcast() for cast in db_warpcasts]

def get_all_warpcasts() -> List[Warpcast]:
    """Get all warpcasts."""
    Model = get_model()
    with get_session() as session:
        db_warpcasts = session.query(Model).all()
        return [cast.to_warpcast() for cast in db_warpcasts]
