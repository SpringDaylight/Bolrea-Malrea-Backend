"""
Database models for Movie Recommendation System
Based on ERD from 프로젝트 착수 보고서
"""
from sqlalchemy import (
    Column, Date, DateTime, Integer, String, Text, Numeric, Float,
    ForeignKey, UniqueConstraint, Index, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from db import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    avatar_text = Column(String, nullable=True, comment="씁쓸한 로맨스, 슬픈 코미디 같은 문구")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    review_likes = relationship("ReviewLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    taste_analysis = relationship("TasteAnalysis", back_populates="user", uselist=False, cascade="all, delete-orphan")
    group_decisions = relationship("GroupDecision", back_populates="owner", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class Movie(Base):
    """영화 메타데이터 테이블"""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    release = Column(Date, nullable=True, comment="개봉일")
    runtime = Column(Integer, nullable=True, comment="러닝타임(분)")
    synopsis = Column(Text, nullable=True, comment="시놉시스")
    poster_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    genres = relationship("MovieGenre", back_populates="movie", cascade="all, delete-orphan")
    tags = relationship("MovieTag", back_populates="movie", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")


class MovieGenre(Base):
    """영화 장르 (다대다 분리)"""
    __tablename__ = "movie_genres"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    genre = Column(String, nullable=False, comment="드라마, 로맨스, SF, 스릴러 등")

    # Relationships
    movie = relationship("Movie", back_populates="genres")

    __table_args__ = (
        Index('ix_movie_genres_movie_genre', 'movie_id', 'genre'),
    )


class MovieTag(Base):
    """영화 정성 태그 (정서/서사/여운)"""
    __tablename__ = "movie_tags"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String, nullable=False, comment="우울, 따뜻, 긴장, 성장, 관계, 여운 김 등")

    # Relationships
    movie = relationship("Movie", back_populates="tags")

    __table_args__ = (
        Index('ix_movie_tags_movie_tag', 'movie_id', 'tag'),
    )


class Review(Base):
    """감상 기록 (리뷰)"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Numeric(2, 1), nullable=False, comment="0.5~5.0, 0.5 단위")
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='uq_user_movie_review'),
        Index('ix_reviews_user_movie', 'user_id', 'movie_id'),
    )


class Comment(Base):
    """리뷰 댓글"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    review = relationship("Review", back_populates="comments")
    user = relationship("User", back_populates="comments")


class ReviewLike(Base):
    """리뷰 좋아요"""
    __tablename__ = "review_likes"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_like = Column(Boolean, nullable=False, default=True, comment="True=좋아요, False=싫어요")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    review = relationship("Review", back_populates="likes")
    user = relationship("User", back_populates="review_likes")

    __table_args__ = (
        UniqueConstraint('review_id', 'user_id', name='uq_review_user_like'),
    )


class TasteAnalysis(Base):
    """취향 분석 결과 (LLM 기반 파생 데이터)"""
    __tablename__ = "taste_analysis"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary_text = Column(Text, nullable=True, comment="당신은 관계 중심 서사와 잔잔하지만 여운이 긴 영화를 선호합니다.")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="taste_analysis")


class GroupDecision(Base):
    """같이 정하기 - 그룹"""
    __tablename__ = "group_decisions"

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_type = Column(String, nullable=False, comment="personal, friends, family")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="group_decisions")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """그룹 멤버"""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("group_decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    group = relationship("GroupDecision", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )


# ============================================
# 벡터 데이터 (파생 데이터, ERD 외부)
# ============================================

class UserPreference(Base):
    """사용자 취향 벡터 (DynamoDB 대신 PostgreSQL 사용)"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    preference_vector_json = Column(JSONB, nullable=False, default=dict, comment="emotion_scores, narrative_traits, ending_preference")
    persona_code = Column(String, nullable=True, comment="사용자 페르소나 코드")
    boost_tags = Column(JSONB, nullable=False, default=list, comment="좋아하는 태그 리스트")
    penalty_tags = Column(JSONB, nullable=False, default=list, comment="싫어하는 태그 리스트")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MovieVector(Base):
    """영화 특성 벡터 (OpenSearch 대신 PostgreSQL 사용)"""
    __tablename__ = "movie_vectors"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    emotion_scores = Column(JSONB, nullable=False, default=dict, comment="감정 태그 점수")
    narrative_traits = Column(JSONB, nullable=False, default=dict, comment="서사 특성 점수")
    ending_preference = Column(JSONB, nullable=False, default=dict, comment="결말 선호도")
    embedding_vector = Column(JSONB, nullable=True, default=list, comment="임베딩 벡터 (향후 벡터 검색용)")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
