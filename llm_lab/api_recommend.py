"""
LLM 기반 영화 추천 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from llm_lab.recommender import LLMRecommender

router = APIRouter(prefix="/api/llm", tags=["llm-recommend"])

# 전역 추천기
recommender = LLMRecommender()


class RecommendRequest(BaseModel):
    user_input: str
    top_k: int = 5
    candidate_pool_size: int = 20
    genres: Optional[List[str]] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class Movie(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    release_year: int
    similarity_score: float
    detail_url: str
    poster_url: Optional[str] = None
    rating: Optional[float] = None


class RecommendResponse(BaseModel):
    recommendations: List[Movie]
    explanation: str
    candidates_count: int
    usage: Optional[dict] = None


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_movies(request: RecommendRequest):
    """
    LLM 기반 영화 추천
    
    - 시스템이 후보 생성 (할루시네이션 방지)
    - LLM이 선택 및 설명
    - 영화 상세 페이지 링크 포함
    """
    try:
        result = recommender.recommend(
            user_input=request.user_input,
            top_k=request.top_k,
            candidate_pool_size=request.candidate_pool_size,
            genres=request.genres,
            year_from=request.year_from,
            year_to=request.year_to
        )
        
        return RecommendResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 오류: {str(e)}")
