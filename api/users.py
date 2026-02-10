"""
User API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from schemas import (
    UserResponse, UserCreate, UserUpdate,
    ReviewResponse, ReviewListResponse,
    TasteAnalysisResponse, MessageResponse
)
from repositories.user import UserRepository
from repositories.review import ReviewRepository

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get current user info"""
    repo = UserRepository(db)
    user = repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        name=user.name,
        avatar_text=user.avatar_text,
        created_at=user.created_at
    )


@router.post("", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    repo = UserRepository(db)
    
    # Check if user already exists
    existing = repo.get(user.id)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_data = user.model_dump()
    db_user = repo.create(user_data)
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        avatar_text=db_user.avatar_text,
        created_at=db_user.created_at
    )


@router.put("/me", response_model=UserResponse)
def update_user(
    user: UserUpdate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update current user"""
    repo = UserRepository(db)
    
    user_data = user.model_dump(exclude_unset=True)
    db_user = repo.update(user_id, user_data)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        avatar_text=db_user.avatar_text,
        created_at=db_user.created_at
    )


@router.get("/me/reviews", response_model=ReviewListResponse)
def get_user_reviews(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get current user's reviews"""
    repo = ReviewRepository(db)
    skip = (page - 1) * page_size
    
    reviews = repo.get_by_user(user_id, skip=skip, limit=page_size)
    total = repo.count(filters={"user_id": user_id})
    
    review_responses = []
    for review in reviews:
        result = repo.get_with_counts(review.id)
        review_responses.append(
            ReviewResponse(
                id=review.id,
                user_id=review.user_id,
                movie_id=review.movie_id,
                rating=review.rating,
                content=review.content,
                created_at=review.created_at,
                likes_count=result["likes_count"],
                comments_count=result["comments_count"]
            )
        )
    
    return ReviewListResponse(reviews=review_responses, total=total)


@router.get("/me/taste-analysis", response_model=TasteAnalysisResponse)
def get_taste_analysis(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user's taste analysis"""
    repo = UserRepository(db)
    taste = repo.get_taste_analysis(user_id)
    
    if not taste:
        raise HTTPException(
            status_code=404,
            detail="Taste analysis not found. Please create reviews first."
        )
    
    return TasteAnalysisResponse(
        user_id=taste.user_id,
        summary_text=taste.summary_text,
        updated_at=taste.updated_at
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    repo = UserRepository(db)
    user = repo.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        name=user.name,
        avatar_text=user.avatar_text,
        created_at=user.created_at
    )
