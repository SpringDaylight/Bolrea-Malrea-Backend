"""
Preference Vector Helper Functions
하위 호환성을 유지하면서 기존/신규 구조를 모두 지원
"""
from typing import Dict, Any, Optional


def is_new_structure(preference_data: Dict[str, Any]) -> bool:
    """
    preference_vector_json이 새 구조인지 확인
    
    새 구조: {"baseline": {...}, "review": {...}, "global": {...}}
    기존 구조: {"emotion_scores": {...}, "narrative_traits": {...}}
    """
    if not preference_data:
        return False
    
    # 새 구조는 baseline, review, global 키를 가짐
    has_new_keys = any(key in preference_data for key in ["baseline", "review", "global"])
    
    # 기존 구조는 emotion_scores, narrative_traits를 직접 가짐
    has_old_keys = any(key in preference_data for key in ["emotion_scores", "narrative_traits"])
    
    return has_new_keys and not has_old_keys


def get_preference_for_recommendation(
    preference_data: Dict[str, Any],
    genre: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    추천에 사용할 취향 벡터 반환
    
    Args:
        preference_data: preference_vector_json
        genre: 특정 장르 (있으면 해당 장르 특화 취향 반환)
    
    Returns:
        - 장르 명시 + 해당 장르 리뷰 있음: baseline + 장르별 리뷰 혼합
        - 장르 명시 없음 or 해당 장르 리뷰 없음: global 반환
        - global 없음: baseline 반환
        - 기존 구조: 그대로 반환
    """
    if not preference_data:
        return None
    
    if is_new_structure(preference_data):
        # 장르가 명시되고, 해당 장르 리뷰가 있으면
        if genre:
            review_genres = preference_data.get("review", {}).get("genres", {})
            if genre in review_genres:
                # baseline + 해당 장르 리뷰 혼합
                return calculate_global(
                    preference_data.get("baseline", {}),
                    review_genres[genre]
                )
        
        # 장르 명시 없거나, 해당 장르 리뷰 없으면 global 사용
        if preference_data.get("global"):
            return preference_data["global"]
        elif preference_data.get("baseline"):
            return preference_data["baseline"]
        else:
            return None
    else:
        # 기존 구조: 그대로 반환
        return preference_data


def migrate_to_new_structure(old_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 구조를 새 구조로 변환
    
    기존: {"emotion_scores": {...}, "narrative_traits": {...}, "ending_preference": {...}}
    변환: {
        "baseline": {기존 데이터},
        "review": {"global": {}, "genres": {}, "review_count": 0},
        "global": null
    }
    """
    if is_new_structure(old_data):
        # 이미 새 구조면 그대로 반환
        return old_data
    
    # 기존 데이터를 baseline으로 이동
    new_structure = {
        "baseline": {
            "emotion_scores": old_data.get("emotion_scores", {}),
            "narrative_traits": old_data.get("narrative_traits", {}),
            "ending_preference": old_data.get("ending_preference", {}),
            "direction_mood": old_data.get("direction_mood", {}),
            "character_relationship": old_data.get("character_relationship", {})
        },
        "review": {
            "global": {
                "emotion_scores": {},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            },
            "genres": {},
            "review_count": 0,
            "last_updated": None
        },
        "global": None  # 추천 시 계산됨
    }
    
    return new_structure


def get_baseline(preference_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    baseline 데이터 반환
    
    - 새 구조: baseline 반환
    - 기존 구조: 전체 데이터 반환 (기존 데이터가 곧 baseline)
    """
    if not preference_data:
        return None
    
    if is_new_structure(preference_data):
        return preference_data.get("baseline")
    else:
        return preference_data


def get_review_data(preference_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    review 데이터 반환
    
    - 새 구조: review 반환
    - 기존 구조: None 반환 (리뷰 데이터 없음)
    """
    if not preference_data:
        return None
    
    if is_new_structure(preference_data):
        return preference_data.get("review")
    else:
        return None


def update_baseline(
    preference_data: Dict[str, Any],
    new_baseline: Dict[str, Any]
) -> Dict[str, Any]:
    """
    baseline만 업데이트하고 review는 보존, global은 재계산
    
    Args:
        preference_data: 기존 preference_vector_json
        new_baseline: 새로운 baseline 데이터
    
    Returns:
        업데이트된 preference_vector_json
    """
    if not preference_data:
        # 데이터가 없으면 새 구조로 생성
        new_data = {
            "baseline": new_baseline,
            "review": {
                "global": {
                    "emotion_scores": {},
                    "narrative_traits": {},
                    "ending_preference": {},
                    "direction_mood": {},
                    "character_relationship": {}
                },
                "genres": {},
                "review_count": 0,
                "last_updated": None
            },
            "global": None
        }
        # global 계산
        new_data["global"] = calculate_global(new_baseline, new_data["review"]["global"])
        return new_data
    
    if is_new_structure(preference_data):
        # 새 구조: baseline만 업데이트
        updated = preference_data.copy()
        updated["baseline"] = new_baseline
        # global 재계산
        updated["global"] = calculate_global(new_baseline, updated["review"]["global"])
        return updated
    else:
        # 기존 구조를 새 구조로 변환하면서 baseline 업데이트
        migrated = migrate_to_new_structure(preference_data)
        migrated["baseline"] = new_baseline
        # global 재계산
        migrated["global"] = calculate_global(new_baseline, migrated["review"]["global"])
        return migrated


def get_structure_info(preference_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    디버깅용: 현재 구조 정보 반환
    """
    if not preference_data:
        return {
            "is_new": False,
            "has_data": False,
            "keys": []
        }
    
    return {
        "is_new": is_new_structure(preference_data),
        "has_data": True,
        "keys": list(preference_data.keys()),
        "has_baseline": "baseline" in preference_data,
        "has_review": "review" in preference_data,
        "has_global": "global" in preference_data,
        "has_emotion_scores": "emotion_scores" in preference_data,
        "has_narrative_traits": "narrative_traits" in preference_data
    }


def calculate_global(
    baseline: Dict[str, Any],
    review_global: Dict[str, Any],
    baseline_weight: float = 0.3,
    review_weight: float = 0.7
) -> Dict[str, Any]:
    """
    baseline과 review.global을 가중평균하여 global 계산
    
    Args:
        baseline: baseline 데이터
        review_global: review.global 데이터
        baseline_weight: baseline 가중치 (기본 0.3)
        review_weight: review 가중치 (기본 0.7)
    
    Returns:
        계산된 global 데이터
    """
    global_data = {
        "emotion_scores": {},
        "narrative_traits": {},
        "ending_preference": {},
        "direction_mood": {},
        "character_relationship": {}
    }
    
    # baseline이 비어있으면 review만 사용
    baseline_empty = not baseline or all(not baseline.get(cat, {}) for cat in global_data.keys())
    # review가 비어있으면 baseline만 사용
    review_empty = not review_global or all(not review_global.get(cat, {}) for cat in global_data.keys())
    
    if baseline_empty and review_empty:
        # 둘 다 비어있으면 빈 global 반환
        return None
    elif baseline_empty:
        # baseline 없으면 review만 사용
        return review_global.copy()
    elif review_empty:
        # review 없으면 baseline만 사용
        return baseline.copy()
    
    # 둘 다 있으면 가중평균
    for category in global_data.keys():
        baseline_cat = baseline.get(category, {})
        review_cat = review_global.get(category, {})
        
        # 모든 태그 수집
        all_tags = set(baseline_cat.keys()) | set(review_cat.keys())
        
        for tag in all_tags:
            baseline_val = baseline_cat.get(tag, 0)
            review_val = review_cat.get(tag, 0)
            
            # 가중평균
            global_data[category][tag] = baseline_val * baseline_weight + review_val * review_weight
    
    return global_data


def update_review_from_analysis(
    preference_data: Dict[str, Any],
    analyzed_preference: Dict[str, Any],
    genre: Optional[str] = None
) -> Dict[str, Any]:
    """
    리뷰 분석 결과로 review 데이터 업데이트, global 재계산
    
    Args:
        preference_data: 기존 preference_vector_json
        analyzed_preference: 리뷰 분석 결과 (5개 카테고리)
        genre: 영화 장르 (있으면 review.genres에도 저장)
    
    Returns:
        업데이트된 preference_vector_json
    """
    from datetime import datetime
    
    # 새 구조가 아니면 마이그레이션
    if not preference_data or not is_new_structure(preference_data):
        preference_data = migrate_to_new_structure(preference_data or {})
    
    updated = preference_data.copy()
    
    # review.global 업데이트 (누적)
    if not updated["review"]["global"]:
        updated["review"]["global"] = {
            "emotion_scores": {},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        }
    
    # 각 카테고리별로 누적 업데이트 (간단한 평균)
    review_count = updated["review"].get("review_count", 0)
    new_count = review_count + 1
    
    for category in ["emotion_scores", "narrative_traits", "ending_preference", "direction_mood", "character_relationship"]:
        if category not in analyzed_preference:
            continue
            
        current_global = updated["review"]["global"].get(category, {})
        new_values = analyzed_preference[category]
        
        # 누적 평균 계산
        for tag, new_score in new_values.items():
            if tag in current_global:
                # 기존 값과 새 값의 가중 평균
                current_global[tag] = (current_global[tag] * review_count + new_score) / new_count
            else:
                # 새로운 태그
                current_global[tag] = new_score
        
        updated["review"]["global"][category] = current_global
    
    # 장르별 데이터 업데이트
    if genre:
        if not updated["review"]["genres"]:
            updated["review"]["genres"] = {}
        
        if genre not in updated["review"]["genres"]:
            updated["review"]["genres"][genre] = {
                "emotion_scores": {},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            }
        
        # 장르별로도 누적 평균 (간단하게 덮어쓰기로 구현)
        for category in ["emotion_scores", "narrative_traits", "ending_preference", "direction_mood", "character_relationship"]:
            if category in analyzed_preference:
                genre_data = updated["review"]["genres"][genre].get(category, {})
                for tag, score in analyzed_preference[category].items():
                    genre_data[tag] = score
                updated["review"]["genres"][genre][category] = genre_data
    
    # 메타데이터 업데이트
    updated["review"]["review_count"] = new_count
    updated["review"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # global 재계산 (baseline + review.global 가중평균)
    updated["global"] = calculate_global(updated["baseline"], updated["review"]["global"])
    
    return updated
