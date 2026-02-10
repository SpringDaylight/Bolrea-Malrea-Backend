"""
User repository with custom queries
"""
from typing import Optional
from sqlalchemy.orm import Session

from models import User, TasteAnalysis
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with custom queries"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_name(self, name: str) -> Optional[User]:
        """Get user by name"""
        return self.db.query(User).filter(User.name == name).first()
    
    def get_taste_analysis(self, user_id: str) -> Optional[TasteAnalysis]:
        """Get user's taste analysis"""
        return (
            self.db.query(TasteAnalysis)
            .filter(TasteAnalysis.user_id == user_id)
            .first()
        )
    
    def update_taste_analysis(self, user_id: str, summary_text: str) -> TasteAnalysis:
        """Update or create taste analysis"""
        taste = self.get_taste_analysis(user_id)
        
        if taste:
            taste.summary_text = summary_text
        else:
            taste = TasteAnalysis(user_id=user_id, summary_text=summary_text)
            self.db.add(taste)
        
        self.db.commit()
        self.db.refresh(taste)
        return taste
