"""
Watched movies repository
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from models import WatchedMovie, Movie


class WatchedMovieRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[WatchedMovie]:
        return (
            self.db.query(WatchedMovie)
            .options(joinedload(WatchedMovie.movie))
            .filter(WatchedMovie.user_id == user_id)
            .order_by(WatchedMovie.watched_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_user(self, user_id: str) -> int:
        return (
            self.db.query(func.count(WatchedMovie.id))
            .filter(WatchedMovie.user_id == user_id)
            .scalar()
        )

    def get(self, user_id: str, movie_id: int) -> Optional[WatchedMovie]:
        return (
            self.db.query(WatchedMovie)
            .filter(WatchedMovie.user_id == user_id, WatchedMovie.movie_id == movie_id)
            .first()
        )

    def create(self, user_id: str, movie_id: int) -> WatchedMovie:
        record = WatchedMovie(user_id=user_id, movie_id=movie_id)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, user_id: str, movie_id: int) -> bool:
        record = self.get(user_id, movie_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
