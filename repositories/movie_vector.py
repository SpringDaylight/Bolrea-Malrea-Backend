"""
Movie vector repository for storing and retrieving movie feature vectors
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from models import MovieVector
from repositories.base import BaseRepository


class MovieVectorRepository(BaseRepository[MovieVector]):
    """Movie vector repository with custom queries"""
    
    def __init__(self, db: Session):
        super().__init__(MovieVector, db)
    
    def get_by_movie_id(self, movie_id: int) -> Optional[MovieVector]:
        """Get movie vector by movie_id"""
        return self.db.query(MovieVector).filter(MovieVector.movie_id == movie_id).first()
    
    def get_by_movie_ids(self, movie_ids: List[int]) -> List[MovieVector]:
        """Get multiple movie vectors by movie_ids"""
        return self.db.query(MovieVector).filter(MovieVector.movie_id.in_(movie_ids)).all()
    
    def upsert(
        self,
        movie_id: int,
        emotion_scores: dict,
        narrative_traits: dict,
        direction_mood: dict,
        character_relationship: dict,
        ending_preference: dict,
        embedding_text: str = None,
        embedding_vector: list = None
    ) -> MovieVector:
        """
        Insert or update movie vector (upsert operation)
        
        Args:
            movie_id: Movie ID
            emotion_scores: Emotion tag scores
            narrative_traits: Narrative trait scores
            direction_mood: Direction/mood scores
            character_relationship: Character relationship scores
            ending_preference: Ending preference scores
            embedding_text: Text for embedding generation
            embedding_vector: Embedding vector (for future use)
        
        Returns:
            MovieVector object
        """
        existing = self.get_by_movie_id(movie_id)
        
        if existing:
            # Update existing vector
            existing.emotion_scores = emotion_scores
            existing.narrative_traits = narrative_traits
            existing.direction_mood = direction_mood
            existing.character_relationship = character_relationship
            existing.ending_preference = ending_preference
            existing.embedding_text = embedding_text
            existing.embedding_vector = embedding_vector or []
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new vector
            new_vector = MovieVector(
                movie_id=movie_id,
                emotion_scores=emotion_scores,
                narrative_traits=narrative_traits,
                direction_mood=direction_mood,
                character_relationship=character_relationship,
                ending_preference=ending_preference,
                embedding_text=embedding_text,
                embedding_vector=embedding_vector or []
            )
            self.db.add(new_vector)
            self.db.commit()
            self.db.refresh(new_vector)
            return new_vector
    
    def delete_by_movie_id(self, movie_id: int) -> bool:
        """Delete movie vector by movie_id"""
        vector = self.get_by_movie_id(movie_id)
        if not vector:
            return False
        
        self.db.delete(vector)
        self.db.commit()
        return True
    
    def exists(self, movie_id: int) -> bool:
        """Check if movie vector exists"""
        return self.db.query(MovieVector).filter(MovieVector.movie_id == movie_id).count() > 0
    
    def count_all(self) -> int:
        """Count total movie vectors"""
        return self.db.query(MovieVector).count()
