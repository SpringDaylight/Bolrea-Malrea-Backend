"""
LLM 기반 영화 추천 API
"""
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from llm_lab.recommender import LLMRecommender
from llm_lab.orchestrator import LLMOrchestrator
from api.deps import get_current_user_optional

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


class SatisfactionRequest(BaseModel):
    movie_id: int
    user_id: Optional[str] = None  # 로그인한 사용자 ID (문자열 UUID)


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
            # 오케스트레이터 방식 - wrap blocking operation in thread pool
            result = await asyncio.to_thread(
                orchestrator.recommend,
                user_input=request.user_input,
                top_k=request.top_k,
                candidate_pool_size=request.candidate_pool_size
            )
            result['method'] = 'orchestrator'
        else:
            # 기존 방식 - wrap blocking operation in thread pool
            result = await asyncio.to_thread(
                recommender.recommend,
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
        from llm_lab.async_client import AsyncLLMClient
        
        llm_client = AsyncLLMClient()
        
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

        explanation = await llm_client.generate_simple(prompt)
        
        return {
            "explanation": explanation,
            "movie_title": request.movie_title
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설명 생성 오류: {str(e)}")


@router.post("/satisfaction")
async def calculate_satisfaction(
    request: SatisfactionRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    사용자 취향과 영화 특성 간의 만족도 확률 계산 (개선된 버전)
    
    JWT 인증을 사용하여 자동으로 사용자 정보를 가져옵니다.
    user_id 파라미터는 하위 호환성을 위해 유지됩니다.
    """
    try:
        from db import SessionLocal
        from models import UserPreference, MovieVector
        from ml.model_sample.analysis.cal_sim import calculate_satisfaction_probability_improved
        from api.deps import get_current_user_optional
        
        # JWT에서 사용자 정보 가져오기 (우선순위 1)
        user_id = None
        if current_user:
            user_id = current_user.id
            print(f"✅ [Satisfaction] JWT에서 사용자 인증: {user_id}")
        # 하위 호환성: request body의 user_id 사용 (우선순위 2)
        elif request.user_id:
            user_id = request.user_id
            print(f"⚠️ [Satisfaction] Body에서 user_id 사용 (deprecated): {user_id}")
        
        # 디버깅 로그
        print(f"🔍 [Satisfaction] Request received:")
        print(f"   - movie_id: {request.movie_id}")
        print(f"   - user_id (final): {user_id}")
        print(f"   - current_user: {current_user.id if current_user else None}")
        
        # Wrap database operations in thread pool
        def _execute_satisfaction_calculation():
            # Wrap SessionLocal() creation
            db = SessionLocal()
            
            try:
                # Wrap database query for movie vector
                movie_vector = db.query(MovieVector).filter(
                    MovieVector.movie_id == request.movie_id
                ).first()
                
                if not movie_vector:
                    raise HTTPException(status_code=404, detail="영화 벡터를 찾을 수 없습니다")
                
                # Wrap database query for user preference (user_id가 있으면)
                if user_id:
                    print(f"✅ [Satisfaction] user_id 있음, DB 조회 시작: {user_id}")
                    user_pref = db.query(UserPreference).filter(
                        UserPreference.user_id == user_id
                    ).first()
                    
                    if not user_pref or not user_pref.preference_vector_json:
                        print(f"❌ [Satisfaction] UserPreference 없음")
                        raise HTTPException(status_code=404, detail="사용자 선호도를 찾을 수 없습니다")
                    
                    print(f"✅ [Satisfaction] UserPreference 찾음")
                    user_profile = user_pref.preference_vector_json
                else:
                    # 로그인하지 않은 경우 에러
                    print(f"❌ [Satisfaction] user_id 없음 - 401 반환")
                    raise HTTPException(status_code=401, detail="로그인이 필요합니다")
                
                # 영화 프로필 구성
                movie_profile = {
                    'emotion_scores': movie_vector.emotion_scores,
                    'narrative_traits': movie_vector.narrative_traits,
                    'ending_preference': movie_vector.ending_preference or {}
                }
                
                # Wrap calculate_satisfaction_probability_improved() call
                result = calculate_satisfaction_probability_improved(
                    user_profile=user_profile,
                    movie_profile=movie_profile,
                    dislikes=user_pref.dislike_tags or [],
                    boost_tags=user_pref.boost_tags or [],
                    use_sigmoid=True,
                    sigmoid_k=6.0,
                    sigmoid_x0=0.5
                )
                
                return {
                    "movie_id": request.movie_id,
                    "satisfaction_probability": result['probability'],
                    "confidence": result['confidence'],
                    "breakdown": result['breakdown'],
                    "user_id": user_id
                }
                
            finally:
                # Ensure proper session cleanup in finally block
                db.close()
        
        # Execute in thread pool to avoid blocking event loop
        return await asyncio.to_thread(_execute_satisfaction_calculation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"만족도 계산 오류: {str(e)}")
