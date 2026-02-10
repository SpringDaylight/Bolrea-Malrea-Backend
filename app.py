"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api import movies, reviews, users, auth
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
    version="1.0.1"
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
