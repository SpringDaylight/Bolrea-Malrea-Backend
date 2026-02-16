"""
User preference repository for storing and retrieving user taste vectors
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models import UserPreference
from repositories.base import BaseRepository


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """User preference repository with custom queries"""
    
    def __init__(self, db: Session):
        super().__init__(UserPreference, db)
    
    def get_by_user_id(self, user_id: str) -> Optional[UserPreference]:
        """Get user preference by user_id"""
        return self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    def upsert(
        self,
        user_id: str,
        preference_vector_json: dict,
        persona_code: Optional[str] = None,
        boost_tags: list = None,
        dislike_tags: list = None,
        penalty_tags: list = None
    ) -> UserPreference:
        """
        Insert or update user preference (upsert operation)
        
        Args:
            user_id: User ID
            preference_vector_json: Dict containing emotion_scores, narrative_traits, etc.
            persona_code: User persona code (optional)
            boost_tags: List of preferred tags
            dislike_tags: List of disliked tags
            penalty_tags: List of penalty tags
        
        Returns:
            UserPreference object
        """
        existing = self.get_by_user_id(user_id)
        
        if existing:
            # Update existing preference
            existing.preference_vector_json = preference_vector_json
            existing.persona_code = persona_code
            existing.boost_tags = boost_tags or []
            existing.dislike_tags = dislike_tags or []
            existing.penalty_tags = penalty_tags or []
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new preference
            new_preference = UserPreference(
                user_id=user_id,
                preference_vector_json=preference_vector_json,
                persona_code=persona_code,
                boost_tags=boost_tags or [],
                dislike_tags=dislike_tags or [],
                penalty_tags=penalty_tags or []
            )
            self.db.add(new_preference)
            self.db.commit()
            self.db.refresh(new_preference)
            return new_preference
    
    def delete_by_user_id(self, user_id: str) -> bool:
        """Delete user preference by user_id"""
        preference = self.get_by_user_id(user_id)
        if not preference:
            return False
        
        self.db.delete(preference)
        self.db.commit()
        return True
