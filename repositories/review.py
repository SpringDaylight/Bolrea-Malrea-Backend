"""
Review repository with custom queries
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from models import Review, ReviewLike, Comment, User
from repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Review repository with custom queries"""
    
    def __init__(self, db: Session):
        super().__init__(Review, db)
    
    def get_by_movie(self, movie_id: int, skip: int = 0, limit: int = 20) -> List[Review]:
        """Get reviews for a movie with user info"""
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.movie_id == movie_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Review]:
        """Get reviews by a user with user info"""
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.user_id == user_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_with_user(self, review_id: int) -> Optional[Review]:
        """Get review with user info"""
        return (
            self.db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.id == review_id)
            .first()
        )
    
    def get_user_review_for_movie(self, user_id: str, movie_id: int) -> Optional[Review]:
        """Get user's review for a specific movie"""
        return (
            self.db.query(Review)
            .filter(Review.user_id == user_id, Review.movie_id == movie_id)
            .first()
        )
    
    def get_with_counts(self, review_id: int) -> Optional[dict]:
        """Get review with like and comment counts and user info"""
        review = self.get_with_user(review_id)
        if not review:
            return None
        
        likes_count = (
            self.db.query(func.count(ReviewLike.id))
            .filter(ReviewLike.review_id == review_id, ReviewLike.is_like == True)
            .scalar()
        )
        
        comments_count = (
            self.db.query(func.count(Comment.id))
            .filter(Comment.review_id == review_id)
            .scalar()
        )
        
        return {
            "review": review,
            "likes_count": likes_count,
            "comments_count": comments_count
        }
    
    def toggle_like(self, review_id: int, user_id: str, is_like: bool = True) -> bool:
        """Toggle like/dislike on a review"""
        existing_like = (
            self.db.query(ReviewLike)
            .filter(ReviewLike.review_id == review_id, ReviewLike.user_id == user_id)
            .first()
        )
        
        if existing_like:
            if existing_like.is_like == is_like:
                # Remove like if same action
                self.db.delete(existing_like)
            else:
                # Update to opposite action
                existing_like.is_like = is_like
        else:
            # Create new like
            new_like = ReviewLike(review_id=review_id, user_id=user_id, is_like=is_like)
            self.db.add(new_like)
        
        self.db.commit()
        return True
    
    def add_comment(
        self,
        review_id: int,
        user_id: str,
        content: str,
        parent_comment_id: Optional[int] = None
    ) -> Comment:
        """Add comment to review (optionally as a reply)"""
        comment = Comment(
            review_id=review_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_comment_id,
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comment(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        return self.db.query(Comment).filter(Comment.id == comment_id).first()

    def update_comment(self, comment_id: int, content: Optional[str]) -> Optional[Comment]:
        """Update comment content"""
        comment = self.get_comment(comment_id)
        if not comment:
            return None

        if content is not None:
            comment.content = content

        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> bool:
        """Delete comment by ID"""
        comment = self.get_comment(comment_id)
        if not comment:
            return False

        self.db.delete(comment)
        self.db.commit()
        return True
    
    def get_comments(self, review_id: int, skip: int = 0, limit: int = 50) -> List[Comment]:
        """Get comments for a review with user info"""
        return (
            self.db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.review_id == review_id)
            .order_by(Comment.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
