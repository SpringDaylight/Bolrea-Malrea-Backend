"""
Phase 1 테스트 스크립트
헬퍼 함수가 기존/신규 구조를 모두 올바르게 처리하는지 확인
"""
from utils.preference_helper import (
    is_new_structure,
    get_preference_for_recommendation,
    migrate_to_new_structure,
    get_baseline,
    get_review_data,
    update_baseline,
    get_structure_info
)

print("=" * 60)
print("Phase 1 테스트: 헬퍼 함수 검증")
print("=" * 60)

# 테스트 1: 기존 구조 인식
print("\n[테스트 1] 기존 구조 인식")
old_structure = {
    "emotion_scores": {"우울": 0.5, "따뜻": 0.7},
    "narrative_traits": {"성장": 0.8, "복수": 0.2},
    "ending_preference": {"happy": 0.6, "open": 0.3, "bittersweet": 0.4}
}
print(f"기존 구조 인식: {is_new_structure(old_structure)}")  # False여야 함
print(f"구조 정보: {get_structure_info(old_structure)}")
assert is_new_structure(old_structure) == False, "기존 구조를 잘못 인식"
print("✅ 통과")

# 테스트 2: 새 구조 인식
print("\n[테스트 2] 새 구조 인식")
new_structure = {
    "baseline": {
        "emotion_scores": {"우울": 0.5, "따뜻": 0.7},
        "narrative_traits": {"성장": 0.8, "복수": 0.2}
    },
    "review": {
        "global": {},
        "genres": {},
        "review_count": 0
    },
    "global": None
}
print(f"새 구조 인식: {is_new_structure(new_structure)}")  # True여야 함
print(f"구조 정보: {get_structure_info(new_structure)}")
assert is_new_structure(new_structure) == True, "새 구조를 잘못 인식"
print("✅ 통과")

# 테스트 3: 기존 구조 → 추천용 데이터 추출
print("\n[테스트 3] 기존 구조에서 추천용 데이터 추출")
rec_data = get_preference_for_recommendation(old_structure)
print(f"추천용 데이터: {rec_data}")
assert rec_data == old_structure, "기존 구조는 그대로 반환되어야 함"
print("✅ 통과")

# 테스트 4: 새 구조 → 추천용 데이터 추출 (global 있음)
print("\n[테스트 4] 새 구조에서 추천용 데이터 추출 (global 있음)")
new_with_global = new_structure.copy()
new_with_global["global"] = {
    "emotion_scores": {"우울": 0.3, "따뜻": 0.8},
    "narrative_traits": {"성장": 0.9, "복수": 0.1}
}
rec_data = get_preference_for_recommendation(new_with_global)
print(f"추천용 데이터: {rec_data}")
assert rec_data == new_with_global["global"], "global이 반환되어야 함"
print("✅ 통과")

# 테스트 5: 새 구조 → 추천용 데이터 추출 (global 없음)
print("\n[테스트 5] 새 구조에서 추천용 데이터 추출 (global 없음)")
rec_data = get_preference_for_recommendation(new_structure)
print(f"추천용 데이터: {rec_data}")
assert rec_data == new_structure["baseline"], "global 없으면 baseline 반환되어야 함"
print("✅ 통과")

# 테스트 6: 기존 구조 → 새 구조 마이그레이션
print("\n[테스트 6] 기존 구조를 새 구조로 마이그레이션")
migrated = migrate_to_new_structure(old_structure)
print(f"마이그레이션 결과:")
print(f"  - baseline: {migrated.get('baseline')}")
print(f"  - review: {migrated.get('review')}")
print(f"  - global: {migrated.get('global')}")
assert is_new_structure(migrated), "마이그레이션 후 새 구조여야 함"
assert migrated["baseline"]["emotion_scores"] == old_structure["emotion_scores"], "baseline에 기존 데이터 보존"
assert migrated["review"]["review_count"] == 0, "review_count 초기화"
assert migrated["global"] is None, "global은 None"
print("✅ 통과")

# 테스트 7: baseline 추출
print("\n[테스트 7] baseline 추출")
baseline_old = get_baseline(old_structure)
baseline_new = get_baseline(new_structure)
print(f"기존 구조 baseline: {baseline_old}")
print(f"새 구조 baseline: {baseline_new}")
assert baseline_old == old_structure, "기존 구조는 전체가 baseline"
assert baseline_new == new_structure["baseline"], "새 구조는 baseline 키 반환"
print("✅ 통과")

# 테스트 8: review 데이터 추출
print("\n[테스트 8] review 데이터 추출")
review_old = get_review_data(old_structure)
review_new = get_review_data(new_structure)
print(f"기존 구조 review: {review_old}")
print(f"새 구조 review: {review_new}")
assert review_old is None, "기존 구조는 review 없음"
assert review_new == new_structure["review"], "새 구조는 review 반환"
print("✅ 통과")

# 테스트 9: baseline 업데이트 (기존 구조)
print("\n[테스트 9] baseline 업데이트 (기존 구조)")
new_baseline_data = {
    "emotion_scores": {"우울": 0.1, "따뜻": 0.9},
    "narrative_traits": {"성장": 0.95, "복수": 0.05},
    "ending_preference": {"happy": 0.8, "open": 0.1, "bittersweet": 0.3}
}
updated = update_baseline(old_structure, new_baseline_data)
print(f"업데이트 결과:")
print(f"  - 새 구조로 변환됨: {is_new_structure(updated)}")
print(f"  - baseline: {updated.get('baseline')}")
assert is_new_structure(updated), "기존 구조는 새 구조로 변환되어야 함"
assert updated["baseline"] == new_baseline_data, "baseline이 업데이트되어야 함"
print("✅ 통과")

# 테스트 10: baseline 업데이트 (새 구조, review 보존)
print("\n[테스트 10] baseline 업데이트 (새 구조, review 보존)")
new_with_review = new_structure.copy()
new_with_review["review"] = {
    "global": {"emotion_scores": {"우울": 0.2}},
    "genres": {"SF": {"emotion_scores": {"긴장": 0.9}}},
    "review_count": 5
}
updated = update_baseline(new_with_review, new_baseline_data)
print(f"업데이트 결과:")
print(f"  - baseline 변경됨: {updated['baseline'] == new_baseline_data}")
print(f"  - review 보존됨: {updated['review']['review_count']}")
assert updated["baseline"] == new_baseline_data, "baseline 업데이트"
assert updated["review"]["review_count"] == 5, "review 데이터 보존"
assert updated["global"] is None, "global은 리셋"
print("✅ 통과")

print("\n" + "=" * 60)
print("✅ Phase 1 모든 테스트 통과!")
print("=" * 60)
print("\n다음 단계:")
print("1. 실제 DB 데이터로 테스트")
print("2. 기존 추천 API가 정상 작동하는지 확인")
print("3. Phase 2로 진행")
