"""
LLM 기반 영화 추천 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from llm_lab.recommender import LLMRecommender
from llm_lab.orchestrator import LLMOrchestrator

router = APIRouter(prefix="/api/llm", tags=["llm-recommend"])

# 전역 추천기
recommender = LLMRecommender()
orchestrator = LLMOrchestrator()


class RecommendRequest(BaseModel):
    user_input: str
    top_k: int = 5
    candidate_pool_size: int = 20
    genres: Optional[List[str]] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    use_orchestrator: bool = False  # 오케스트레이터 사용 여부


class Movie(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    release_year: int
    similarity_score: float  # 프론트 호환성 (final_score와 동일)
    final_score: Optional[float] = None  # 최종 점수 (가중치 + 보너스)
    weighted_score: Optional[float] = None  # 가중치 적용 점수
    keyword_score: Optional[float] = None  # 키워드 점수
    emotion_score: Optional[float] = None  # 감성 점수
    sources: Optional[List[str]] = None  # 검색 소스 (keyword, vector)
    detail_url: str
    poster_url: Optional[str] = None
    rating: Optional[float] = None
    reason: Optional[str] = None  # 개별 추천 이유


class RecommendResponse(BaseModel):
    recommendations: List[Movie]
    explanation: str
    candidates_count: int
    usage: Optional[dict] = None
    method: str = "basic"  # basic or orchestrator


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_movies(request: RecommendRequest):
    """
    LLM 기반 영화 추천
    
    - use_orchestrator=False: 기존 방식 (하이브리드 검색 + LLM 선택)
    - use_orchestrator=True: 오케스트레이터 방식 (LLM 컨트롤러)
    """
    try:
        if request.use_orchestrator:
            # 오케스트레이터 방식
            result = orchestrator.recommend(
                user_input=request.user_input,
                top_k=request.top_k,
                candidate_pool_size=request.candidate_pool_size
            )
            result['method'] = 'orchestrator'
        else:
            # 기존 방식
            result = recommender.recommend(
                user_input=request.user_input,
                top_k=request.top_k,
                candidate_pool_size=request.candidate_pool_size,
                genres=request.genres,
                year_from=request.year_from,
                year_to=request.year_to
            )
            result['method'] = 'basic'
        
        return RecommendResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 오류: {str(e)}")
