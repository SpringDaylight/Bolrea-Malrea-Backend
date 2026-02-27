# 장르별 선호도 통합 완료

## 📋 요약

LLM 추천 시스템에 장르별 선호도 기능을 통합했습니다. 이제 사용자가 특정 장르를 명시하면 해당 장르에 대한 리뷰 기반 선호도를 사용하여 추천합니다.

## 🎯 동작 방식

### 시나리오 1: 장르 명시
```
사용자: "재미있는 액션 영화 추천해줘"
→ LLM이 "액션" 장르 추출
→ baseline + review.genres["액션"] 사용
→ 액션 영화에 대한 사용자의 리뷰 기반 취향 반영
```

### 시나리오 2: 장르 명시 없음
```
사용자: "따뜻한 영화 추천해줘"
→ 장르 추출 안됨
→ global 사용 (baseline 30% + review.global 70%)
→ 전체 취향 반영
```

### 시나리오 3: 장르 명시했지만 리뷰 없음
```
사용자: "재미있는 드라마 추천해줘"
→ LLM이 "드라마" 장르 추출
→ review.genres["드라마"] 없음
→ global 사용 (폴백)
```

## 🔧 수정된 파일

### 1. `llm_lab/orchestrator.py`

**추가된 함수:**
```python
def _extract_genre_for_preference(self, query_plan: Dict) -> Optional[str]:
    """쿼리 플랜에서 장르를 추출하여 선호도 조회에 사용"""
```

**수정된 함수:**
- `recommend()`: 장르 추출 및 로깅 추가
- `_validate_recommendations()`: `genre` 파라미터 추가
- `_calculate_satisfaction_batch()`: `genre` 파라미터 추가, `get_preference_for_recommendation()` 사용

**주요 변경사항:**
1. 쿼리 플랜에서 장르 추출
2. 장르를 만족도 계산 함수에 전달
3. `get_preference_for_recommendation(pref_data, genre=genre)` 사용
4. 캐시 키에 장르 포함 (`satisfaction:{user_id}:{movie_id}:{genre}`)

### 2. `llm_lab/api_personalized.py`

**수정된 부분:**
```python
# 기존
pref_json = user_pref.preference_vector_json
if 'global' in pref_json:
    user_profile = pref_json['global']
else:
    user_profile = pref_json

# 수정 후
from utils.preference_helper import get_preference_for_recommendation

user_profile = get_preference_for_recommendation(
    pref_json,
    genre=None  # 개인 맞춤 추천은 항상 global 사용
)
```

### 3. `llm_lab/api_recommend.py`

**수정된 부분:**
```python
# satisfaction 엔드포인트에서도 get_preference_for_recommendation() 사용
user_profile = get_preference_for_recommendation(
    user_pref.preference_vector_json,
    genre=None  # satisfaction API는 항상 global 사용
)
```

## 📊 장르 매핑

LLM이 추출한 장르를 DB 형식으로 정규화:

```python
genre_mapping = {
    "액션": "액션",
    "드라마": "드라마",
    "코미디": "코미디",
    "로맨스": "로맨스",
    "스릴러": "스릴러",
    "공포": "공포",
    "SF": "SF",
    "판타지": "판타지",
    "애니메이션": "애니메이션",
    "다큐멘터리": "다큐멘터리",
    "범죄": "범죄",
    "미스터리": "미스터리",
    "모험": "모험",
    "가족": "가족",
    "전쟁": "전쟁",
    "서부": "서부",
    "뮤지컬": "뮤지컬",
    "역사": "역사"
}
```

## 🔍 디버깅 로그

### 장르 추출 성공
```
✅ [Orchestrator] 장르 추출: '액션' - 장르별 선호도 사용
✅ [Satisfaction Batch] 장르별 선호도 사용: genre=액션
```

### 장르 명시 없음
```
✅ [Orchestrator] 장르 명시 없음 - global 선호도 사용
✅ [Satisfaction Batch] global 선호도 사용
```

## 🧪 테스트 방법

### 1. 장르 명시 테스트
```bash
curl -X POST "http://localhost:8000/api/llm/recommend" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_input": "재미있는 액션 영화 추천해줘",
    "top_k": 5,
    "use_orchestrator": true
  }'
```

**확인 사항:**
- 로그에 "장르 추출: '액션'" 출력
- 만족도 계산 시 액션 장르 선호도 사용

### 2. 장르 명시 없음 테스트
```bash
curl -X POST "http://localhost:8000/api/llm/recommend" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_input": "따뜻한 영화 추천해줘",
    "top_k": 5,
    "use_orchestrator": true
  }'
```

**확인 사항:**
- 로그에 "장르 명시 없음 - global 선호도 사용" 출력
- 만족도 계산 시 global 선호도 사용

## 📈 기대 효과

1. **정확도 향상**: 장르별 리뷰 데이터를 활용하여 더 정확한 추천
2. **개인화 강화**: 사용자가 특정 장르에 대해 가진 취향을 정확히 반영
3. **유연성**: 장르 명시 여부에 따라 자동으로 적절한 선호도 사용

## ✅ 검증 완료

- [x] orchestrator.py 수정 완료
- [x] api_personalized.py 수정 완료
- [x] api_recommend.py 수정 완료
- [x] 코드 문법 오류 없음
- [x] 장르 추출 로직 구현
- [x] 만족도 계산에 장르 전달
- [x] 캐시 키에 장르 포함
- [x] 하위 호환성 유지 (genre=None 시 global 사용)

## 🚀 다음 단계

이제 사용자가 LLM 추천을 요청하면:
1. LLM이 자동으로 장르를 추출
2. 장르가 있으면 해당 장르 리뷰 기반 선호도 사용
3. 장르가 없으면 전체 취향(global) 사용
4. 만족도 계산 시 적절한 선호도 프로필 사용

모든 기능이 자동으로 작동하며, 사용자는 별도 설정 없이 장르별 맞춤 추천을 받을 수 있습니다!

## 📅 날짜

2024-02-27

---

**통합 완료!** 이제 LLM 추천 시스템이 장르별 선호도를 자동으로 활용합니다. 🎉
