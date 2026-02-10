"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    name: str
    avatar_text: Optional[str] = None


class UserCreate(UserBase):
    id: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_text: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Movie Schemas
# ============================================

class MovieBase(BaseModel):
    title: str
    release: Optional[date] = None
    runtime: Optional[int] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    release: Optional[date] = None
    runtime: Optional[int] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None


class MovieResponse(MovieBase):
    id: int
    created_at: datetime
    genres: List[str] = []
    tags: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    movies: List[MovieResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Review Schemas
# ============================================

class ReviewBase(BaseModel):
    rating: Decimal = Field(..., ge=0.5, le=5.0, description="0.5~5.0, 0.5 단위")
    content: Optional[str] = None


class ReviewCreate(ReviewBase):
    movie_id: int


class ReviewUpdate(BaseModel):
    rating: Optional[Decimal] = Field(None, ge=0.5, le=5.0)
    content: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int
    user_id: str
    movie_id: int
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int


# ============================================
# Comment Schemas
# ============================================

class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    review_id: int


class CommentResponse(CommentBase):
    id: int
    review_id: int
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Like Schemas
# ============================================

class LikeCreate(BaseModel):
    review_id: int
    is_like: bool = True


class LikeResponse(BaseModel):
    id: int
    review_id: int
    user_id: str
    is_like: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Taste Analysis Schemas
# ============================================

class TasteAnalysisResponse(BaseModel):
    user_id: str
    summary_text: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# User Preference Schemas (ML)
# ============================================

class UserPreferenceResponse(BaseModel):
    user_id: str
    preference_vector_json: Dict[str, Any]
    persona_code: Optional[str] = None
    boost_tags: List[str] = []
    penalty_tags: List[str] = []
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Movie Vector Schemas (ML)
# ============================================

class MovieVectorResponse(BaseModel):
    movie_id: int
    emotion_scores: Dict[str, float]
    narrative_traits: Dict[str, float]
    ending_preference: Dict[str, float]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Generic Response
# ============================================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
