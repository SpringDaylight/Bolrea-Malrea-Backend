"""
User Preferences API
Endpoints for saving and retrieving user taste preferences
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from db import get_db
from repositories.user_preference import UserPreferenceRepository
from schemas import UserPreferenceResponse, MessageResponse
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/user-preferences", tags=["User Preferences"])


# ============================================
# Request Schemas
# ============================================

class SaveUserPreferenceRequest(BaseModel):
    """Request schema for saving user preference"""
    user_id: str = Field(..., description="User ID")
    preference_vector_json: Dict[str, Any] = Field(
        ...,
        description="Preference vector containing emotion_scores, narrative_traits, direction_mood, character_relationship, ending_preference"
    )
    persona_code: str = Field(None, description="User persona code")
    boost_tags: List[str] = Field(default_factory=list, description="List of liked tags")
    dislike_tags: List[str] = Field(default_factory=list, description="List of disliked tags")
    penalty_tags: List[str] = Field(default_factory=list, description="List of penalty tags")


# ============================================
# Endpoints
# ============================================

@router.get("/{user_id}", response_model=UserPreferenceResponse)
def get_user_preference(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user preference by user_id
    
    Returns the saved user taste preference including:
    - preference_vector_json: emotion_scores, narrative_traits, etc.
    - boost_tags: liked tags
    - dislike_tags: disliked tags
    - penalty_tags: penalty tags
    """
    repo = UserPreferenceRepository(db)
    preference = repo.get_by_user_id(user_id)
    
    if not preference:
        raise HTTPException(
            status_code=404,
            detail=f"User preference not found for user_id: {user_id}"
        )
    
    return UserPreferenceResponse(
        user_id=preference.user_id,
        preference_vector_json=preference.preference_vector_json,
        persona_code=preference.persona_code,
        boost_tags=preference.boost_tags,
        penalty_tags=preference.penalty_tags,
        updated_at=preference.updated_at
    )


@router.post("", response_model=UserPreferenceResponse, status_code=201)
def save_user_preference(
    request: SaveUserPreferenceRequest,
    db: Session = Depends(get_db)
):
    """
    Save or update user preference (upsert)
    
    If preference exists for the user, it will be updated.
    Otherwise, a new preference will be created.
    
    Request body should include:
    - user_id: User identifier
    - preference_vector_json: Complete preference vector
    - boost_tags: List of liked tags (optional)
    - dislike_tags: List of disliked tags (optional)
    - penalty_tags: List of penalty tags (optional)
    """
    repo = UserPreferenceRepository(db)
    
    preference = repo.upsert(
        user_id=request.user_id,
        preference_vector_json=request.preference_vector_json,
        persona_code=request.persona_code,
        boost_tags=request.boost_tags,
        dislike_tags=request.dislike_tags,
        penalty_tags=request.penalty_tags
    )
    
    return UserPreferenceResponse(
        user_id=preference.user_id,
        preference_vector_json=preference.preference_vector_json,
        persona_code=preference.persona_code,
        boost_tags=preference.boost_tags,
        penalty_tags=preference.penalty_tags,
        updated_at=preference.updated_at
    )


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user_preference(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete user preference by user_id
    """
    repo = UserPreferenceRepository(db)
    
    if not repo.exists(user_id):
        raise HTTPException(
            status_code=404,
            detail=f"User preference not found for user_id: {user_id}"
        )
    
    success = repo.delete_by_user_id(user_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user preference"
        )
    
    return MessageResponse(message=f"User preference deleted for user_id: {user_id}")


@router.get("/{user_id}/exists")
def check_user_preference_exists(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if user preference exists
    """
    repo = UserPreferenceRepository(db)
    exists = repo.exists(user_id)
    
    return {
        "user_id": user_id,
        "exists": exists
    }
