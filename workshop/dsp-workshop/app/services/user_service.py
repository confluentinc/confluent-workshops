import logging
from sqlalchemy.orm import Session
from app.models.models import User, CartItem

logger = logging.getLogger(__name__)

class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    def get_or_create_user(db: Session, name: str, email: str) -> User:
        """Get existing user or create new one"""
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {email}")
        return user 