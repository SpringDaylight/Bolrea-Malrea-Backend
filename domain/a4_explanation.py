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
    description.py 스타일로 수정: 첫 문장에 확률 제거, 자연어 중심
    
    Args:
        prediction_result: A-3의 결과
        movie_title: 영화 제목
        user_liked_tags: 좋아하는 태그
        user_disliked_tags: 싫어하는 태그
    
    Returns:
        자연어 설명
    """
    prob = prediction_result.get("probability", 0)
    breakdown = prediction_result.get("breakdown", {})
    top_factors = breakdown.get("top_factors", ["정서 톤", "서사 초점"])
    
    # 30% 이하: 부정적 설명
    if prob <= 0.30:
        explanation = f'"{movie_title}"은 당신의 취향과 맞지 않을 수 있습니다. '
        explanation += f'{top_factors[0] if top_factors else "정서"} 측면에서 차이가 있어요. '
        
        if user_disliked_tags and len(user_disliked_tags) > 0:
            explanation += f'특히 당신이 선호하지 않는 {user_disliked_tags[0]} 요소가 포함되어 있습니다. '
    
    # 30-70%: 중립적 설명
    elif prob <= 0.70:
        explanation = f'"{movie_title}"은 당신의 취향과 어느 정도 맞을 수 있습니다. '
        explanation += f'{top_factors[0] if top_factors else "정서"} 측면에서 흥미로운 포인트가 있어요. '
        
        if user_liked_tags and len(user_liked_tags) > 0:
            explanation += f'당신이 좋아하는 {user_liked_tags[0]} 요소가 일부 포함되어 있습니다. '
    
    # 70% 이상: 긍정적 설명
    else:
        explanation = f'"{movie_title}"은 당신의 취향과 잘 맞을 것 같아요. '
        explanation += f'{top_factors[0] if top_factors else "정서"} 측면에서 특히 좋은 포인트가 있습니다. '
        
        if user_liked_tags and len(user_liked_tags) > 0:
            explanation += f'당신이 좋아하는 {user_liked_tags[0]} 요소가 강하게 나타나요. '
    
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
    
    # 캐시 키 생성: explanation_detail:{movie_title}:{probability_rounded}
    # probability를 반올림하여 유사한 확률은 같은 캐시 사용
    prob_rounded = round(probability, 2)
    cache_key = f"explanation_detail:{movie_title}:{prob_rounded}"
    
    # 캐시 확인
    cached_result = cache_get(cache_key)
    if cached_result:
        print(f"✅ [ExplainDetail] Cache hit: {cache_key}")
        return cached_result
    
    print(f"🔍 [ExplainDetail] Cache miss, generating: {cache_key}")
    
    # 예측 결과 재구성
    prediction_result = {
        "probability": probability,
        "breakdown": breakdown
    }
    
    # LLM 기반 설명 생성 시도 (_build_explanation_prompt 사용)
    try:
        from ml.model_sample.analysis.description import (
            get_bedrock_client, 
            _build_explanation_prompt,
            _build_factor_hints
        )
        import json
        
        bedrock_client = get_bedrock_client()
        
        # 프롬프트 생성
        top_factors = prediction_result.get("breakdown", {}).get("top_factors", ["정서 톤", "서사 초점"])[:2]
        factor_hints = _build_factor_hints(
            top_factors=top_factors,
            user_liked_tags=user_liked_tags,
            user_disliked_tags=user_disliked_tags,
        )
        
        prompt = _build_explanation_prompt(
            prediction_result=prediction_result,
            movie_title=movie_title,
            user_liked_tags=user_liked_tags,
            user_disliked_tags=user_disliked_tags,
            factor_hints=factor_hints,
        )
        
        if bedrock_client:
            # Bedrock을 통한 LLM 호출
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3
            }
            
            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                explanation = response_body['content'][0]['text'].strip()
                # 설명 문구에서 퍼센트 수치 제거 (예: "87%", "79%")
                import re
                explanation = re.sub(r'\d+%', '', explanation)
                explanation = explanation.strip()
            else:
                explanation = _generate_template_explanation(
                    prediction_result,
                    movie_title,
                    user_liked_tags,
                    user_disliked_tags
                )
        else:
            # Bedrock 없으면 템플릿 사용
            explanation = _generate_template_explanation(
                prediction_result,
                movie_title,
                user_liked_tags,
                user_disliked_tags
            )
    except Exception as e:
        print(f"⚠️  LLM 설명 생성 실패, 템플릿 사용: {e}")
        # LLM 실패 시 템플릿 fallback
        explanation = _generate_template_explanation(
            prediction_result,
            movie_title,
            user_liked_tags,
            user_disliked_tags
        )
    
    # 주요 요소 추출 (차원별 일치율 - 내부 계산용, 프론트엔드에서는 표시 안 함)
    if breakdown:
        emotion_sim   = breakdown.get("emotion_similarity", 0)
        narrative_sim = breakdown.get("narrative_similarity", 0)
        direction_sim = breakdown.get("direction_mood_similarity", breakdown.get("ending_similarity", 0))
    
    result = {
        "movie_title": movie_title,
        "match_rate": round(probability * 100, 1),
        "explanation": explanation,
        "disclaimer": "추천은 정서·서사 태그 분석 기반이며 개인차가 있을 수 있습니다."
    }
    
    # 캐시에 저장 (TTL 24시간 - 설명은 자주 바뀌지 않음)
    cache_set(cache_key, result, ttl=86400)
    print(f"✅ [ExplainDetail] Cached result: {cache_key}")
    
    return result
