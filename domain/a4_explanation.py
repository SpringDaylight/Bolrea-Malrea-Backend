"""
A-4: 설명 가능한 추천
만족 확률 결과를 자연어로 설명
"""
from typing import Dict, List
import os
import boto3


def _generate_template_explanation(
    prediction_result: Dict,
    movie_title: str,
    user_liked_tags: List[str] = None,
    user_disliked_tags: List[str] = None
) -> str:
    """
    템플릿 기반 설명 생성 (LLM 없이도 작동)

    Args:
        prediction_result: A-3의 결과
        movie_title: 영화 제목
        user_liked_tags: 좋아하는 태그
        user_disliked_tags: 싫어하는 태그

    Returns:
        자연어 설명
    """
    prob = prediction_result.get("probability", 0) * 100
    breakdown = prediction_result.get("breakdown", {})
    top_factors = breakdown.get("top_factors", ["취향 요소"])

    if prob <= 30:
        explanation = f'"{movie_title}"은 당신의 취향과 잘 맞지 않을 수 있습니다. '
        explanation += f'{", ".join(top_factors)} 측면에서 차이가 있습니다. '

        if user_disliked_tags and len(user_disliked_tags) > 0:
            explanation += f'특히 당신이 선호하지 않는 {", ".join(user_disliked_tags[:3])} 요소가 포함되어 있습니다. '

    elif prob <= 70:
        explanation = f'"{movie_title}"은 당신의 취향과 {prob:.0f}% 일치합니다. '
        explanation += f'{", ".join(top_factors)} 측면에서 어느 정도 맞을 수 있습니다. '

        if user_liked_tags and len(user_liked_tags) > 0:
            explanation += f'당신이 좋아하는 {", ".join(user_liked_tags[:2])} 요소가 일부 포함되어 있습니다. '

    else:
        explanation = f'"{movie_title}"은 당신의 취향과 {prob:.0f}% 일치합니다! '
        explanation += f'특히 {", ".join(top_factors)} 측면에서 잘 맞습니다. '

        if user_liked_tags and len(user_liked_tags) > 0:
            explanation += f'당신이 좋아하는 {", ".join(user_liked_tags[:3])} 요소가 강하게 나타납니다. '

    explanation += '이 예측은 정서·서사 분석 기반이므로 개인차가 있을 수 있습니다.'

    return explanation


def explain_prediction(payload: dict) -> dict:
    """
    A-4: 설명 가능한 추천 (캐싱 적용)

    Args:
        payload: {
            "movie_title": str,
            "match_rate": float (0-100),
            "probability": float (0-1),
            "breakdown": Dict,
            "user_liked_tags": List[str] (선택),
            "user_disliked_tags": List[str] (선택)
        }

    Returns:
        {
            "movie_title": str,
            "match_rate": float,
            "explanation": str,
            "key_factors": List[Dict],
            "disclaimer": str
        }
    """
    from utils.cache import cache_get, cache_set
    import hashlib
    import json

    movie_title = payload.get("movie_title", "Unknown")
    match_rate = payload.get("match_rate", 0.0)
    probability = payload.get("probability", match_rate / 100.0)
    breakdown = payload.get("breakdown", {})
    user_liked_tags = payload.get("user_liked_tags", [])
    user_disliked_tags = payload.get("user_disliked_tags", [])

    prob_rounded = round(probability, 2)
    cache_key = f"explanation_detail:v2:{movie_title}:{prob_rounded}"

    cached_result = cache_get(cache_key)
    if cached_result:
        cached_result["key_factors"] = []
        print(f"✅ [ExplainDetail] Cache hit: {cache_key}")
        return cached_result

    print(f"🔍 [ExplainDetail] Cache miss, generating: {cache_key}")

    prediction_result = {
        "probability": probability,
        "breakdown": breakdown
    }

    try:
        from ml.model_sample.analysis.description import generate_explanation, get_bedrock_client

        bedrock_client = get_bedrock_client()
        if bedrock_client:
            explanation = generate_explanation(
                prediction_result=prediction_result,
                movie_title=movie_title,
                user_liked_tags=user_liked_tags,
                user_disliked_tags=user_disliked_tags,
                bedrock_client=bedrock_client
            )
        else:
            explanation = _generate_template_explanation(
                prediction_result,
                movie_title,
                user_liked_tags,
                user_disliked_tags
            )
    except Exception as e:
        print(f"⚠️  LLM 설명 생성 실패, 템플릿 사용: {e}")
        explanation = _generate_template_explanation(
            prediction_result,
            movie_title,
            user_liked_tags,
            user_disliked_tags
        )

    # 상세 페이지에는 자연어 설명만 노출하고 세부 유사도 수치는 숨긴다.
    key_factors = []

    result = {
        "movie_title": movie_title,
        "match_rate": round(match_rate, 2),
        "explanation": explanation,
        "key_factors": key_factors,
        "disclaimer": "추천은 정서·서사 태그 분석 기반이며 개인차가 있을 수 있습니다."
    }

    cache_set(cache_key, result, ttl=86400)
    print(f"✅ [ExplainDetail] Cached result: {cache_key}")

    return result
