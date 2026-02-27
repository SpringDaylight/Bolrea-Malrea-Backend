"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api import movies, reviews, users, auth, gamification, cocktail
from utils.validator import validate_request

from domain.a1_preference import analyze_preference
from domain.a2_movie_vector import process_movie_vector
from domain.a3_prediction import predict_satisfaction
from domain.a4_explanation import explain_prediction
from domain.a5_emotional_search import emotional_search
from domain.a6_group_simulation import simulate_group
from domain.a7_taste_map import build_taste_map

# Create FastAPI app
app = FastAPI(
    title="Movie Recommendation API",
    description="정서·서사 기반 영화 취향 시뮬레이션 & 감성 검색 서비스",
    version="1.0.8"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(movies.router)
app.include_router(reviews.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(gamification.router)
app.include_router(cocktail.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Movie Recommendation API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check for load balancer"""
    return {"status": "healthy"}


@app.post("/analyze/preference")
def analyze_preference_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a1_preference_request.json", body)
        return analyze_preference(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/movie/vector")
def movie_vector_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a2_movie_vector_request.json", body)
        return process_movie_vector(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/predict/satisfaction")
def predict_satisfaction_endpoint(body: dict) -> dict:
    try:
<<<<<<< Updated upstream
=======
        from db import SessionLocal
        from models import UserPreference
        
        # user_id가 있으면 DB에서 조회
        user_id = body.get("user_id")
        if user_id:
            db = SessionLocal()
            try:
                user_pref = db.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).first()
                
                if not user_pref or not user_pref.preference_vector_json:
                    raise HTTPException(status_code=404, detail="사용자 선호도를 찾을 수 없습니다")
                
                # preference_vector_json에서 global 프로필 추출
                pref_json = user_pref.preference_vector_json
                if 'global' in pref_json:
                    # 신 형식: global 키가 있는 경우
                    user_profile = pref_json['global']
                else:
                    # 구 형식: 최상위에 직접 있는 경우
                    user_profile = pref_json
                
                # DB에서 가져온 프로필로 교체
                body["user_profile"] = user_profile
                body["dislike_tags"] = user_pref.dislikes or []
                body["boost_tags"] = user_pref.boost_tags or []
            finally:
                db.close()
        
        # 기존 로직 실행
>>>>>>> Stashed changes
        body = validate_request("a3_predict_request.json", body)
        return predict_satisfaction(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/explain/prediction")
def explain_prediction_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a4_explain_request.json", body)
        return explain_prediction(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/search/emotional")
def emotional_search_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a5_search_request.json", body)
        return emotional_search(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/group/simulate")
def group_simulate_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a6_group_request.json", body)
        return simulate_group(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/map/taste")
def taste_map_endpoint(body: dict) -> dict:
    try:
        body = validate_request("a7_map_request.json", body)
        return build_taste_map(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
