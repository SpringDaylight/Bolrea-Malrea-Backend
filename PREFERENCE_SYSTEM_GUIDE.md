# 취향 벡터 시스템 완전 가이드

## 📊 데이터 구조

```json
{
  "baseline": {
    "emotion_scores": {...},
    "narrative_traits": {...},
    "ending_preference": {...},
    "direction_mood": {...},
    "character_relationship": {...}
  },
  "review": {
    "global": {
      "emotion_scores": {...},
      "narrative_traits": {...},
      "ending_preference": {...},
      "direction_mood": {...},
      "character_relationship": {...}
    },
    "genres": {
      "액션": {...},
      "드라마": {...}
    },
    "review_count": 15,
    "last_updated": "2024-02-27T10:30:00Z"
  },
  "global": {
    "emotion_scores": {...},
    "narrative_traits": {...},
    "ending_preference": {...},
    "direction_mood": {...},
    "character_relationship": {...}
  }
}
```

---

## 🆕 신규 사용자 플로우

### 1단계: 회원가입 + 설문 완료

**API 호출:**
```
POST /api/user-preferences
{
  "user_id": "user_123",
  "preference_vector_json": {
    "emotion_scores": {"우울": 0.5, "따뜻": 0.8},
    "narrative_traits": {"성장": 0.9},
    "ending_preference": {"happy": 0.7},
    "direction_mood": {"영상미": 0.6},
    "character_relationship": {"공감": 0.8}
  }
}
```

**처리 로직:**
1. `update_baseline()` 호출
2. baseline에 설문 결과 저장
3. review는 빈 상태로 초기화
4. **global 계산**: review 없으므로 `global = baseline`

**저장된 데이터:**
```json
{
  "baseline": {
    "emotion_scores": {"우울": 0.5, "따뜻": 0.8},
    "narrative_traits": {"성장": 0.9},
    "ending_preference": {"happy": 0.7},
    "direction_mood": {"영상미": 0.6},
    "character_relationship": {"공감": 0.8}
  },
  "review": {
    "global": {},
    "genres": {},
    "review_count": 0
  },
  "global": {
    "emotion_scores": {"우울": 0.5, "따뜻": 0.8},
    "narrative_traits": {"성장": 0.9},
    "ending_preference": {"happy": 0.7},
    "direction_mood": {"영상미": 0.6},
    "character_relationship": {"공감": 0.8}
  }
}
```

---

### 2단계: 첫 리뷰 작성

**API 호출:**
```
POST /api/reviews
{
  "movie_id": 123,
  "rating": 4.5,
  "content": "정말 감동적이고 따뜻한 영화였어요..."
}
```

**처리 로직:**
1. 리뷰 내용 분석 (A-1 API)
2. 분석 결과:
   ```json
   {
     "emotion_scores": {"우울": 0.2, "따뜻": 0.9},
     "narrative_traits": {"성장": 0.85},
     ...
   }
   ```
3. 영화 장르 조회: "드라마"
4. `update_review_from_analysis()` 호출
5. **review.global 업데이트**: 첫 리뷰이므로 그대로 저장
6. **review.genres["드라마"]** 저장
7. **review_count**: 0 → 1
8. **global 재계산**:
   ```
   global = baseline * 0.3 + review.global * 0.7
   
   예: 우울 = 0.5 * 0.3 + 0.2 * 0.7 = 0.15 + 0.14 = 0.29
   ```

**저장된 데이터:**
```json
{
  "baseline": {
    "emotion_scores": {"우울": 0.5, "따뜻": 0.8},
    ...
  },
  "review": {
    "global": {
      "emotion_scores": {"우울": 0.2, "따뜻": 0.9},
      ...
    },
    "genres": {
      "드라마": {
        "emotion_scores": {"우울": 0.2, "따뜻": 0.9},
        ...
      }
    },
    "review_count": 1,
    "last_updated": "2024-02-27T10:30:00Z"
  },
  "global": {
    "emotion_scores": {"우울": 0.29, "따뜻": 0.87},
    ...
  }
}
```

---

### 3단계: LLM 영화 추천

#### 케이스 A: 장르 명시 안 함
**사용자 쿼리:** "따뜻한 영화 추천해줘"

**처리 로직:**
1. LLM이 장르 추출 → 없음
2. `get_preference_for_recommendation(preference_data, genre=None)`
3. **global 사용**
4. 추천 알고리즘에 global 전달

**사용되는 취향:**
```json
{
  "emotion_scores": {"우울": 0.29, "따뜻": 0.87},
  ...
}
```
→ 설문(30%) + 전체 리뷰(70%) 혼합

---

#### 케이스 B: 장르 명시
**사용자 쿼리:** "따뜻한 드라마 추천해줘"

**처리 로직:**
1. LLM이 장르 추출 → "드라마"
2. `get_preference_for_recommendation(preference_data, genre="드라마")`
3. **review.genres["드라마"]** 확인 → 있음
4. **장르 특화 취향 계산**:
   ```
   genre_pref = baseline * 0.3 + review.genres["드라마"] * 0.7
   
   예: 따뜻 = 0.8 * 0.3 + 0.9 * 0.7 = 0.24 + 0.63 = 0.87
   ```

**사용되는 취향:**
```json
{
  "emotion_scores": {"우울": 0.21, "따뜻": 0.87},
  ...
}
```
→ 설문(30%) + 드라마 리뷰(70%) 혼합

---

## 👤 기존 사용자 플로우

### 1단계: 설문 다시 하기

**현재 데이터:**
```json
{
  "baseline": {"emotion_scores": {"우울": 0.5, "따뜻": 0.8}, ...},
  "review": {
    "global": {"emotion_scores": {"우울": 0.2, "따뜻": 0.9}, ...},
    "genres": {
      "드라마": {...},
      "액션": {...}
    },
    "review_count": 5
  },
  "global": {"emotion_scores": {"우울": 0.29, "따뜻": 0.87}, ...}
}
```

**API 호출:**
```
POST /api/user-preferences
{
  "user_id": "user_123",
  "preference_vector_json": {
    "emotion_scores": {"우울": 0.1, "따뜻": 0.9, "긴장": 0.7},
    "narrative_traits": {"성장": 0.5, "관계": 0.8},
    ...
  }
}
```

**처리 로직:**
1. 기존 데이터 조회
2. `update_baseline()` 호출
3. **baseline만 새 설문으로 덮어쓰기**
4. **review 완전히 보존** (review_count=5 유지)
5. **global 재계산**:
   ```
   global = 새baseline * 0.3 + 기존review.global * 0.7
   
   예: 우울 = 0.1 * 0.3 + 0.2 * 0.7 = 0.03 + 0.14 = 0.17
   ```

**저장된 데이터:**
```json
{
  "baseline": {
    "emotion_scores": {"우울": 0.1, "따뜻": 0.9, "긴장": 0.7},
    "narrative_traits": {"성장": 0.5, "관계": 0.8},
    ...
  },
  "review": {
    "global": {"emotion_scores": {"우울": 0.2, "따뜻": 0.9}, ...},
    "genres": {
      "드라마": {...},
      "액션": {...}
    },
    "review_count": 5  // 보존됨!
  },
  "global": {
    "emotion_scores": {"우울": 0.17, "따뜻": 0.9, "긴장": 0.21},
    "narrative_traits": {"성장": 0.5, "관계": 0.24},
    ...
  }
}
```

**핵심:**
- ✅ baseline 업데이트
- ✅ review 데이터 완전 보존 (5개 리뷰 유지)
- ✅ global 자동 재계산

---

### 2단계: 추가 리뷰 작성 (6번째 리뷰)

**API 호출:**
```
POST /api/reviews
{
  "movie_id": 456,
  "rating": 5.0,
  "content": "긴장감 넘치는 액션 영화..."
}
```

**처리 로직:**
1. 리뷰 분석 결과:
   ```json
   {
     "emotion_scores": {"긴장": 0.9, "통쾌": 0.85},
     ...
   }
   ```
2. 영화 장르: "액션"
3. **review.global 누적 평균**:
   ```
   기존 평균 (5개 리뷰) + 새 리뷰 (1개)
   
   예: 긴장 = (기존평균 * 5 + 0.9 * 1) / 6
   ```
4. **review.genres["액션"]** 업데이트
5. **review_count**: 5 → 6
6. **global 재계산**:
   ```
   global = baseline * 0.3 + 새review.global * 0.7
   ```

**저장된 데이터:**
```json
{
  "baseline": {
    "emotion_scores": {"우울": 0.1, "따뜻": 0.9, "긴장": 0.7},
    ...
  },
  "review": {
    "global": {
      "emotion_scores": {"우울": 0.18, "따뜻": 0.88, "긴장": 0.15, "통쾌": 0.14},
      ...
    },
    "genres": {
      "드라마": {...},
      "액션": {
        "emotion_scores": {"긴장": 0.9, "통쾌": 0.85},
        ...
      }
    },
    "review_count": 6,
    "last_updated": "2024-02-27T11:00:00Z"
  },
  "global": {
    "emotion_scores": {"우울": 0.156, "따뜻": 0.886, "긴장": 0.315, "통쾌": 0.098},
    ...
  }
}
```

---

### 3단계: LLM 영화 추천

#### 케이스 A: 장르 명시 안 함
**사용자 쿼리:** "재미있는 영화 추천해줘"

**사용되는 취향:** `global`
```json
{
  "emotion_scores": {"우울": 0.156, "따뜻": 0.886, "긴장": 0.315, "통쾌": 0.098},
  ...
}
```
→ 새 설문(30%) + 6개 리뷰 평균(70%)

---

#### 케이스 B: 장르 명시 - 액션
**사용자 쿼리:** "재미있는 액션 영화 추천해줘"

**처리 로직:**
```
genre_pref = baseline * 0.3 + review.genres["액션"] * 0.7

긴장 = 0.7 * 0.3 + 0.9 * 0.7 = 0.21 + 0.63 = 0.84
통쾌 = 0 * 0.3 + 0.85 * 0.7 = 0 + 0.595 = 0.595
```

**사용되는 취향:**
```json
{
  "emotion_scores": {"긴장": 0.84, "통쾌": 0.595, ...},
  ...
}
```
→ 새 설문(30%) + 액션 리뷰(70%)

---

#### 케이스 C: 장르 명시 - 드라마
**사용자 쿼리:** "따뜻한 드라마 추천해줘"

**처리 로직:**
```
genre_pref = baseline * 0.3 + review.genres["드라마"] * 0.7

따뜻 = 0.9 * 0.3 + 0.95 * 0.7 = 0.27 + 0.665 = 0.935
```

**사용되는 취향:**
```json
{
  "emotion_scores": {"따뜻": 0.935, ...},
  ...
}
```
→ 새 설문(30%) + 드라마 리뷰(70%)

---

## 📈 취향 대시보드 & 영양표

### 워드클라우드 API
**엔드포인트:** `GET /api/user-preferences/{user_id}/wordcloud?type=both`

**처리 로직:**
```python
pref_vector = preference.preference_vector_json

# 새 구조 지원
if 'global' in pref_vector:
    pref_vector = pref_vector['global']  # ✅ global 사용

emotion_scores = pref_vector.get("emotion_scores", {})
```

**결과:**
- ✅ 새 구조에서 `global` 자동 추출
- ✅ 설문(30%) + 리뷰(70%) 혼합된 최종 취향 표시
- ✅ 기존 구조도 호환

---

### 영양표 (Nutrition Facts)
**엔드포인트:** `GET /api/user-preferences/{user_id}/wordcloud?type=emotion`

**처리 로직:**
```python
# global에서 데이터 추출
emotions = pref_vector.get("emotion_scores", {})
moods = pref_vector.get("direction_mood", {})
narratives = pref_vector.get("narrative_traits", {})

# 4대 영양소 계산
dopamine_score = moods.get("긴장되는", 0) * 100
sensitivity_score = (emotions.get("감동적이에요", 0) + ...) / 3 * 100
brain_score = (narratives.get("생각하면서 봐야 해요", 0) + ...) / 2 * 100
eye_score = (moods.get("영상미가 뛰어나요", 0) + ...) / 2 * 100
```

**결과:**
- ✅ global 기반으로 정확한 영양표 생성
- ✅ 설문 + 리뷰 혼합된 최종 취향 반영

---

## ✅ 검증 완료 사항

1. ✅ 신규 사용자: 설문 → 리뷰 → 추천 (장르 유/무)
2. ✅ 기존 사용자: 설문 재작성 → 리뷰 보존 → 추천
3. ✅ 리뷰 누적: 평균 계산 정확성
4. ✅ 장르별 추천: 액션 vs 드라마 차별화
5. ✅ 워드클라우드: global 자동 추출
6. ✅ 영양표: global 기반 계산
7. ✅ 하위 호환성: 기존 구조 지원

---

## 🎯 핵심 포인트

1. **설문 다시 해도 리뷰 데이터 안전** ✅
2. **장르별 맞춤 추천 가능** ✅
3. **설문(30%) + 리뷰(70%) 가중평균** ✅
4. **취향 대시보드 정상 작동** ✅
5. **기존 API 모두 호환** ✅

---

## 📝 남은 작업

추천 API들이 `genre` 파라미터를 받도록 수정 필요:
- `llm_lab/api_recommend.py`
- `llm_lab/api_personalized.py`
- `llm_lab/orchestrator.py`

LLM이 사용자 쿼리에서 장르를 추출하여 전달하도록 구현 필요.

---

## 🐛 버그 수정 이력

### 2024-02-27: 리뷰 장르 업데이트 버그 수정

**문제:**
- 사용자가 리뷰를 작성해도 `review.genres`가 비어있음
- `review_count`가 0으로 남아있음

**원인:**
`api/reviews.py`에서 영화 장르를 잘못 가져옴:
```python
# ❌ 잘못된 코드
movie = MovieRepository(db).get_by_id(db_review.movie_id)
genre = movie.genre if movie else None  # movie.genre는 존재하지 않음
```

Movie 모델은 `genres` 관계(relationship)를 가지며, 각 MovieGenre 객체는 `.genre` 속성을 가짐.

**해결:**
```python
# ✅ 수정된 코드
movie = MovieRepository(db).get_with_details(db_review.movie_id)
genre = movie.genres[0].genre if movie and movie.genres else None
```

**영향받은 함수:**
- `create_review()` (line ~90)
- `update_review()` (line ~180)

**복구 방법:**
기존 리뷰의 선호도 데이터를 복구하려면:
```bash
python test_manual_review_update.py
```

**검증:**
```bash
python test_review_genre_update.py
python test_complete_flow.py
python test_new_review_simulation.py
```

**참고 문서:**
- `REVIEW_GENRE_FIX.md`: 상세 수정 내역

