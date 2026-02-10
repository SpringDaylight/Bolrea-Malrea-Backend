"""
Review API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from schemas import (
    ReviewResponse, ReviewListResponse, ReviewCreate, ReviewUpdate,
    CommentResponse, CommentCreate, MessageResponse
)
from repositories.review import ReviewRepository

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get review by ID with counts"""
    repo = ReviewRepository(db)
    result = repo.get_with_counts(review_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review = result["review"]
    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        movie_id=review.movie_id,
        rating=review.rating,
        content=review.content,
        created_at=review.created_at,
        likes_count=result["likes_count"],
        comments_count=result["comments_count"]
    )


@router.post("", response_model=ReviewResponse, status_code=201)
def create_review(
    review: ReviewCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new review"""
    repo = ReviewRepository(db)
    
    # Check if user already reviewed this movie
    existing = repo.get_user_review_for_movie(user_id, review.movie_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already reviewed this movie. Use PUT to update."
        )
    
    review_data = review.model_dump()
    review_data["user_id"] = user_id
    
    db_review = repo.create(review_data)
    
    return ReviewResponse(
        id=db_review.id,
        user_id=db_review.user_id,
        movie_id=db_review.movie_id,
        rating=db_review.rating,
        content=db_review.content,
        created_at=db_review.created_at,
        likes_count=0,
        comments_count=0
    )


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review: ReviewUpdate,
    db: Session = Depends(get_db)
):
    """Update a review"""
    repo = ReviewRepository(db)
    
    review_data = review.model_dump(exclude_unset=True)
    db_review = repo.update(review_id, review_data)
    
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    result = repo.get_with_counts(review_id)
    
    return ReviewResponse(
        id=db_review.id,
        user_id=db_review.user_id,
        movie_id=db_review.movie_id,
        rating=db_review.rating,
        content=db_review.content,
        created_at=db_review.created_at,
        likes_count=result["likes_count"],
        comments_count=result["comments_count"]
    )


@router.delete("/{review_id}", response_model=MessageResponse)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review"""
    repo = ReviewRepository(db)
    
    if not repo.delete(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    
    return MessageResponse(message="Review deleted successfully")


@router.post("/{review_id}/likes", response_model=MessageResponse)
def toggle_like(
    review_id: int,
    user_id: str = Query(..., description="User ID"),
    is_like: bool = Query(True, description="True for like, False for dislike"),
    db: Session = Depends(get_db)
):
    """Toggle like/dislike on a review"""
    repo = ReviewRepository(db)
    
    # Check if review exists
    if not repo.get(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    
    repo.toggle_like(review_id, user_id, is_like)
    
    action = "liked" if is_like else "disliked"
    return MessageResponse(message=f"Review {action} successfully")


@router.get("/{review_id}/comments", response_model=List[CommentResponse])
def get_comments(
    review_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get comments for a review"""
    repo = ReviewRepository(db)
    
    # Check if review exists
    if not repo.get(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    
    comments = repo.get_comments(review_id, skip=skip, limit=limit)
    
    return [
        CommentResponse(
            id=comment.id,
            review_id=comment.review_id,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at
        )
        for comment in comments
    ]


@router.post("/{review_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    review_id: int,
    comment: CommentCreate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Add a comment to a review"""
    repo = ReviewRepository(db)
    
    # Check if review exists
    if not repo.get(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    
    db_comment = repo.add_comment(review_id, user_id, comment.content)
    
    return CommentResponse(
        id=db_comment.id,
        review_id=db_comment.review_id,
        user_id=db_comment.user_id,
        content=db_comment.content,
        created_at=db_comment.created_at
    )
