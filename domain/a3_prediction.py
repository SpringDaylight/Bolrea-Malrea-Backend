"""
A-3: 만족 확률 계산 (사용자 취향 vs 영화 특성 매칭)

- 감정/서사/결말 벡터 코사인 유사도
- 좋아하는 태그 보너스, 싫어하는 태그 페널티
- 최종 점수 -> 확률/신뢰도 산출
"""

import math
from typing import Dict, List


def _cosine_sim(a: List[float], b: List[float]) -> float:
    # 방향 유사도 계산 (크기 무관)
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _align_vector(d: Dict[str, float], keys: List[str]) -> List[float]:
    return [float(d.get(k, 0.0)) for k in keys]


def _calculate_dislike_penalty(movie_profile: Dict, dislikes: List[str]) -> float:
    # 싫어하는 태그가 영화 프로필에 포함될수록 페널티 증가
    penalty = 0.0
    categories = ["emotion_scores", "narrative_traits", "direction_mood", "character_relationship"]
    for category in categories:
        if category in movie_profile:
            for tag in dislikes:
                if tag in movie_profile[category]:
                    penalty += float(movie_profile[category][tag])
    return penalty


def _calculate_boost_score(movie_profile: Dict, boost_tags: List[str]) -> float:
    # 좋아하는 태그가 영화 프로필에 포함될수록 보너스 증가
    boost = 0.0
    categories = ["emotion_scores", "narrative_traits", "direction_mood", "character_relationship"]
    for category in categories:
        if category in movie_profile:
            for tag in boost_tags:
                if tag in movie_profile[category]:
                    boost += float(movie_profile[category][tag])
    return boost


def _top_factors(sim_e: float, sim_n: float, sim_d: float) -> List[str]:
    factors = [
        ("정서 톤", sim_e),
        ("서사 초점", sim_n),
        ("결말 취향", sim_d),
    ]
    factors.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in factors[:2]]


def calculate_satisfaction_probability(
    user_profile: Dict,
    movie_profile: Dict,
    dislikes: List[str] | None = None,
    boost_tags: List[str] | None = None,
    weights: Dict[str, float] | None = None,
    penalty_weight: float = 0.7,
    boost_weight: float = 0.5,
) -> Dict:
    # 입력 누락 시 기본값 보정
    if dislikes is None:
        dislikes = []
    if boost_tags is None:
        boost_tags = []
    if weights is None:
        weights = {"emotion": 0.5, "narrative": 0.3, "ending": 0.2}

    e_keys = list(user_profile.get("emotion_scores", {}).keys())
    n_keys = list(user_profile.get("narrative_traits", {}).keys())
    d_keys = list(user_profile.get("ending_preference", {}).keys())

    # 1) 차원별 코사인 유사도 계산
    sim_e = _cosine_sim(
        _align_vector(user_profile.get("emotion_scores", {}), e_keys),
        _align_vector(movie_profile.get("emotion_scores", {}), e_keys),
    )
    sim_n = _cosine_sim(
        _align_vector(user_profile.get("narrative_traits", {}), n_keys),
        _align_vector(movie_profile.get("narrative_traits", {}), n_keys),
    )
    sim_d = _cosine_sim(
        _align_vector(user_profile.get("ending_preference", {}), d_keys),
        _align_vector(movie_profile.get("ending_preference", {}), d_keys),
    )

    # 2) 보너스/페널티 계산
    boost_score = _calculate_boost_score(movie_profile, boost_tags)
    dislike_penalty = _calculate_dislike_penalty(movie_profile, dislikes)

    w_e = weights.get("emotion", 0.5)
    w_n = weights.get("narrative", 0.3)
    w_d = weights.get("ending", 0.2)

    # 3) 가중치 합산 + 보너스/페널티 적용
    raw_score = (
        (w_e * sim_e + w_n * sim_n + w_d * sim_d)
        + (boost_weight * boost_score)
        - (penalty_weight * dislike_penalty)
    )

    # 4) -1~1 점수를 0~1 확률로 변환
    probability = (raw_score + 1) / 2
    probability = max(0.0, min(1.0, probability))

    # 5) 차원 간 분산이 낮을수록 신뢰도 높게 설정
    sims = [sim_e, sim_n, sim_d]
    mean = sum(sims) / len(sims)
    variance = sum((x - mean) ** 2 for x in sims) / len(sims)
    confidence = 1 - min(math.sqrt(variance), 1.0)

    breakdown = {
        "emotion_similarity": round(sim_e, 3),
        "narrative_similarity": round(sim_n, 3),
        "ending_similarity": round(sim_d, 3),
        "boost_score": round(boost_score, 3),
        "dislike_penalty": round(dislike_penalty, 3),
        "top_factors": _top_factors(sim_e, sim_n, sim_d),
    }

    return {
        "probability": round(probability, 3),
        "confidence": round(confidence, 3),
        "raw_score": round(raw_score, 3),
        "breakdown": breakdown,
    }


def predict_satisfaction(payload: dict) -> dict:
    """
    A-3: 사용자 + 영화 -> 만족 확률 계산
    """
    # payload에서 사용자/영화 프로필 및 태그 정보 추출
    user_profile = payload.get("user_profile", {})
    movie_profile = payload.get("movie_profile", {})
    dislikes = payload.get("dislike_tags") or user_profile.get("dislike_tags") or []
    boost_tags = payload.get("boost_tags") or user_profile.get("boost_tags") or []

    result = calculate_satisfaction_probability(
        user_profile=user_profile,
        movie_profile=movie_profile,
        dislikes=dislikes,
        boost_tags=boost_tags,
    )

    return {
        "movie_id": movie_profile.get("movie_id"),
        "title": movie_profile.get("title", "Unknown"),
        "probability": result["probability"],
        "confidence": result["confidence"],
        "raw_score": result["raw_score"],
        "match_rate": round(result["probability"] * 100, 2),
        "breakdown": result["breakdown"],
    }
