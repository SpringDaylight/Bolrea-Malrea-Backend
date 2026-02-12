"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )


# ============================================
# User Schemas
# ============================================

class UserBase(BaseSchema):
    name: str
    avatar_text: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[str] = None


class UserCreate(UserBase):
    id: str


class UserUpdate(BaseSchema):
    name: Optional[str] = None
    avatar_text: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime


class UserSignupRequest(BaseSchema):
    user_id: str
    name: str
    nickname: str
    email: str
    password: str
    password_confirm: str


class UserLoginRequest(BaseSchema):
    user_id: str
    password: str


# ============================================
# Movie Schemas
# ============================================

class MovieBase(BaseSchema):
    title: str
    release: Optional[date] = None
    runtime: Optional[int] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseSchema):
    title: Optional[str] = None
    release: Optional[date] = None
    runtime: Optional[int] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None


class MovieResponse(MovieBase):
    id: int
    created_at: datetime
    avg_rating: Optional[Decimal] = None
    genres: List[str] = []
    tags: List[str] = []



class MovieListResponse(BaseSchema):
    movies: List[MovieResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Review Schemas
# ============================================

class ReviewBase(BaseSchema):
    rating: Decimal = Field(..., ge=0.5, le=5.0, description="0.5~5.0, 0.5 단위")
    content: Optional[str] = None


class ReviewCreate(ReviewBase):
    movie_id: int


class ReviewUpdate(BaseSchema):
    rating: Optional[Decimal] = Field(None, ge=0.5, le=5.0)
    content: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int
    user_id: str
    movie_id: int
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0



class ReviewListResponse(BaseSchema):
    reviews: List[ReviewResponse]
    total: int


# ============================================
# Comment Schemas
# ============================================

class CommentBase(BaseSchema):
    content: str


class CommentCreate(CommentBase):
    review_id: int


class CommentResponse(CommentBase):
    id: int
    review_id: int
    user_id: str
    created_at: datetime


# ============================================
# Like Schemas
# ============================================

class LikeCreate(BaseSchema):
    review_id: int
    is_like: bool = True


class LikeResponse(BaseSchema):
    id: int
    review_id: int
    user_id: str
    is_like: bool
    created_at: datetime


# ============================================
# Taste Analysis Schemas
# ============================================

class TasteAnalysisResponse(BaseSchema):
    user_id: str
    summary_text: Optional[str] = None
    updated_at: datetime


# ============================================
# User Preference Schemas (ML)
# ============================================

class UserPreferenceResponse(BaseSchema):
    user_id: str
    preference_vector_json: Dict[str, Any]
    persona_code: Optional[str] = None
    boost_tags: List[str] = []
    penalty_tags: List[str] = []
    updated_at: datetime


# ============================================
# Movie Vector Schemas (ML)
# ============================================

class MovieVectorResponse(BaseSchema):
    movie_id: int
    emotion_scores: Dict[str, float]
    narrative_traits: Dict[str, float]
    ending_preference: Dict[str, float]
    updated_at: datetime


# ============================================
# Generic Response
# ============================================

class MessageResponse(BaseSchema):
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseSchema):
    error: str
    detail: Optional[str] = None
