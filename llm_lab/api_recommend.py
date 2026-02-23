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


class ExplainRequest(BaseModel):
    user_input: str
    movie_title: str
    movie_synopsis: Optional[str] = None
    genres: Optional[List[str]] = None
    keyword_score: Optional[float] = None
    emotion_score: Optional[float] = None
    final_score: Optional[float] = None


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
    synopsis: Optional[str] = None  # 시놉시스
    reason: Optional[str] = None  # 개별 추천 이유
    is_selected: Optional[bool] = None  # 최종 선택 여부
    not_selected_reason: Optional[str] = None  # 선택되지 않은 이유


class RecommendResponse(BaseModel):
    recommendations: List[Movie]
    explanation: str
    candidates_count: int
    usage: Optional[dict] = None
    method: str = "basic"  # basic or orchestrator
    keyword_candidates: Optional[List[Movie]] = None  # 키워드 후보군
    vector_candidates: Optional[List[Movie]] = None  # 벡터 후보군
    keyword_weight: Optional[float] = None  # 키워드 가중치
    emotion_weight: Optional[float] = None  # 감성 가중치


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


@router.post("/explain")
async def explain_recommendation(request: ExplainRequest):
    """
    특정 영화 추천 이유를 LLM으로 상세 설명
    """
    try:
        from llm_lab.client import LLMClient
        
        llm_client = LLMClient()
        
        # 점수 정보 포맷팅
        score_info = ""
        if request.final_score is not None:
            score_info += f"\n- 최종 점수: {request.final_score * 100:.1f}%"
        if request.keyword_score is not None and request.keyword_score > 0:
            score_info += f"\n- 키워드 매칭: {request.keyword_score * 100:.1f}%"
        if request.emotion_score is not None and request.emotion_score > 0:
            score_info += f"\n- 감성 유사도: {request.emotion_score * 100:.1f}%"
        
        # 장르 정보
        genre_info = ""
        if request.genres:
            genre_info = f"\n- 장르: {', '.join(request.genres)}"
        
        # 시놉시스 정보
        synopsis_info = ""
        if request.movie_synopsis:
            synopsis_info = f"\n- 줄거리: {request.movie_synopsis[:200]}..."
        
        prompt = f"""사용자가 "{request.user_input}"라고 요청했을 때, 
영화 "{request.movie_title}"을(를) 추천한 이유를 자세히 설명해주세요.

영화 정보:{genre_info}{synopsis_info}

점수 정보:{score_info}

다음 내용을 포함해서 2-3문단으로 설명해주세요:
1. 이 영화가 사용자 요청과 어떻게 관련되는지
2. 영화의 어떤 특징이 사용자의 니즈를 충족시키는지
3. 점수가 높은/낮은 이유 (키워드 매칭, 감성 유사도 등)

친근하고 자연스러운 톤으로 작성해주세요."""

        explanation = llm_client.generate_simple(prompt)
        
        return {
            "explanation": explanation,
            "movie_title": request.movie_title
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설명 생성 오류: {str(e)}")
