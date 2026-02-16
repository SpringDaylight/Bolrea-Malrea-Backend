# 프론트 → 백엔드 AI/ML API 시나리오

이 문서는 프론트엔드가 API를 호출했을 때 **실제로 어떤 로직이 수행되고 어떤 응답이 오는지**를 시나리오별로 정리합니다.  
현재 코드 기준으로 `app.py`에 연결된 **A-1 ~ A-7 ML 엔드포인트**와, `/api/*`로 제공되는 **게이미피케이션/칵테일 기능**을 함께 설명합니다.

> 참고: `utils/validator.validate_request()`는 **JSON 객체인지 여부만 확인**하며 스키마 타입 검증은 하지 않습니다.

---

## 프론트 UI → API 호출 매핑 (현재 백엔드 기준)
> 프론트엔드 코드가 이 저장소에 없어서 **버튼/화면 명칭은 추정**입니다.  
> 실제 화면명은 프론트 구현과 맞춰 교체하면 됩니다.

| 화면/버튼(추정) | 호출 API | 후속/의존 | 비고 |
| --- | --- | --- | --- |
| 취향 분석하기 | `POST /analyze/preference` | 없음 | A-1 결과를 프론트가 보관 |
| 영화 벡터화(관리/백오피스) | `POST /movie/vector` | 없음 | A-2 결과를 프론트가 보관 |
| 만족도 계산 | `POST /predict/satisfaction` | A-1, A-2 결과 필요 | A-3 |
| 추천 설명 보기 | `POST /explain/prediction` | A-3 결과 필요 | A-4 |
| 감성 검색 | `POST /search/emotional` | 검색 엔진 호출은 별도 | A-5는 쿼리만 반환 |
| 그룹 추천 시뮬레이션 | `POST /group/simulate` | 구성원 프로필 필요 | A-6 |
| 취향 지도 보기 | `POST /map/taste` | 없음 | A-7 |
| 감정 칵테일 생성 | `POST /api/cocktail` | 없음 | Bedrock 사용 |
| 리뷰 작성(게이미피케이션) | `POST /api/review` | 없음 | DEMO 사용자 고정 |
| 홈 화면 | `GET /api/home` | 없음 | 레벨/팝콘/질문 |
| 밥주기 룰렛 | `POST /api/feeding` | 없음 | 하루 1회 제한 |
| 오늘의 질문 답변 | `POST /api/question/answer` | 없음 | 질문 히스토리 갱신 |
| 질문 히스토리 | `GET /api/history` | 없음 | |
| 상점 보기 | `GET /api/shop` | 없음 | |
| 테마 구매 | `POST /api/shop/buy` | 팝콘 보유 | |
| 테마 적용 | `POST /api/shop/apply` | 보유 테마 필요 | |
| 인벤토리 조회 | `GET /api/inventory` | 없음 | |
| 그룹 추천(게이미피케이션) | `POST /api/group/recommend` | 별도 입력 포맷 | A-6과 유사 목적 |

추가로 일반 콘텐츠 화면(영화/리뷰 리스트)은 다음 API가 사용됩니다.
| 화면/버튼(추정) | 호출 API | 비고 |
| --- | --- | --- |
| 영화 리스트 | `GET /api/movies` | 검색/장르/정렬 파라미터 |
| 영화 상세 | `GET /api/movies/{movie_id}` | |
| 영화 리뷰 리스트 | `GET /api/movies/{movie_id}/reviews` | |
| 리뷰 CRUD | `POST/PUT/DELETE /api/reviews` | |
| 리뷰 좋아요/싫어요 | `POST /api/reviews/{review_id}/likes` | |
| 리뷰 댓글 CRUD | `/api/reviews/{review_id}/comments` | |

---

## A-1 ~ A-7 (app.py에 직접 연결된 ML 엔드포인트)

### 시나리오 A-1. 사용자 취향 분석
요청: `POST /analyze/preference`  
파일: `app.py`, `domain/a1_preference.py`

요청 예시:
```json
{
  "text": "감동적이고 따뜻한 영화 좋아해요",
  "dislikes": "무서운 거 싫어"
}
```

백엔드 처리 흐름:
1. `validate_request("a1_preference_request.json", body)` (형식만 확인)
2. `domain.a1_preference.analyze_preference()` 호출
3. 택소노미 로드 → 해시 기반 점수 생성
4. 규칙 기반 부정어 감지로 `dislike_tags`, `boost_tags` 생성

응답 예시(요약):
```json
{
  "user_text": "...",
  "emotion_scores": {"감동적이에요": 0.83, "...": 0.12},
  "narrative_traits": {"반전이 많아요": 0.42, "...": 0.07},
  "ending_preference": {"happy": 0.63, "open": 0.41, "bittersweet": 0.29},
  "dislike_tags": ["무서워요"],
  "boost_tags": ["따뜻해요", "감동적이에요"]
}
```

메모:
- LLM 사용 안 함 (해시 기반 deterministic 점수)
- 부정어 처리도 규칙 기반 fallback만 사용

---

### 시나리오 A-2. 영화 벡터화
요청: `POST /movie/vector`  
파일: `app.py`, `domain/a2_movie_vector.py`

요청 예시:
```json
{
  "movie_id": 123,
  "title": "인생은 아름다워",
  "overview": "2차 세계대전 중...",
  "genres": ["드라마", "전쟁"]
}
```

백엔드 처리 흐름:
1. `validate_request("a2_movie_vector_request.json", body)`
2. `domain.a2_movie_vector.process_movie_vector()` 실행
3. 영화 텍스트 합성 → 해시 기반 점수 생성
4. `embedding_text` 생성, `embedding`은 빈 배열로 반환

응답 예시(요약):
```json
{
  "movie_id": 123,
  "title": "인생은 아름다워",
  "emotion_scores": { ... },
  "narrative_traits": { ... },
  "direction_mood": { ... },
  "character_relationship": { ... },
  "ending_preference": { "happy": 0.61, "open": 0.27, "bittersweet": 0.44 },
  "embedding_text": "Title: ... Emotions: ... Narrative: ...",
  "embedding": []
}
```

---

### 시나리오 A-3. 만족 확률 계산
요청: `POST /predict/satisfaction`  
파일: `app.py`, `domain/a3_prediction.py`

요청 예시:
```json
{
  "user_profile": { "...": "A-1 결과" },
  "movie_profile": { "...": "A-2 결과" },
  "dislike_tags": ["무서워요"],
  "boost_tags": ["감동적이에요"]
}
```

백엔드 처리 흐름:
1. `validate_request("a3_predict_request.json", body)`
2. 코사인 유사도 + 보너스/페널티 계산
3. `probability`, `confidence`, `breakdown` 구성

응답 예시(요약):
```json
{
  "movie_id": 123,
  "title": "인생은 아름다워",
  "probability": 0.82,
  "confidence": 0.91,
  "raw_score": 0.64,
  "match_rate": 82.0,
  "breakdown": {
    "emotion_similarity": 0.90,
    "narrative_similarity": 0.76,
    "ending_similarity": 0.71,
    "boost_score": 0.12,
    "dislike_penalty": 0.05,
    "top_factors": ["정서 톤", "서사 초점"]
  }
}
```

---

### 시나리오 A-4. 설명 생성
요청: `POST /explain/prediction`  
파일: `app.py`, `domain/a4_explanation.py`

요청 예시:
```json
{
  "movie_title": "인생은 아름다워",
  "match_rate": 82.0,
  "key_factors": [
    {"category": "emotion", "tag": "감동적이에요", "score": 0.9}
  ]
}
```

백엔드 처리 흐름:
1. 템플릿 기반 설명 문구 생성
2. 상위 요소를 자연어로 요약

응답 예시(요약):
```json
{
  "movie_title": "인생은 아름다워",
  "match_rate": 82.0,
  "explanation": "...",
  "key_factors": [...],
  "disclaimer": "추천은 정서·서사 태그 분석 기반이며..."
}
```

---

### 시나리오 A-5. 감성 검색 쿼리 생성
요청: `POST /search/emotional`  
파일: `app.py`, `domain/a5_emotional_search.py`

요청 예시:
```json
{
  "text": "우울한데 너무 무겁지 않은 영화",
  "genres": ["드라마"],
  "year_from": 2010
}
```

백엔드 처리 흐름:
1. 텍스트 키워드 → 감정 태그 점수 매핑
2. 하이브리드 검색용 쿼리(JSON) 생성

응답 예시(요약):
```json
{
  "intent": "search",
  "expanded_query": {"emotion_scores": {...}},
  "hybrid_query": {
    "query": {"bool": {"must": [], "filter": [...] }},
    "knn": {"field": "emotion_vector", "query_vector": [...], "k": 50, "num_candidates": 200}
  }
}
```

메모:
- 실제 검색 실행은 하지 않고, **검색용 payload만 반환**합니다.

---

### 시나리오 A-6. 그룹 시뮬레이션
요청: `POST /group/simulate`  
파일: `app.py`, `domain/a6_group_simulation.py`

요청 예시:
```json
{
  "members": [
    {"user_id": "u1", "profile": { "...": "A-1 결과" }},
    {"user_id": "u2", "profile": { "...": "A-1 결과" }}
  ],
  "movie_profile": { "...": "A-2 결과" },
  "strategy": "least_misery"
}
```

백엔드 처리 흐름:
1. 각 멤버 만족 확률 계산 (A-3 로직 호출)
2. 전략에 따라 그룹 점수 계산  
   - `least_misery`: 최소값  
   - `average`: 평균값

응답 예시(요약):
```json
{
  "group_score": 0.68,
  "strategy": "least_misery",
  "members": [
    {"user_id": "u1", "probability": 0.70, "confidence": 0.9, "level": "만족"},
    {"user_id": "u2", "probability": 0.68, "confidence": 0.88, "level": "보통"}
  ],
  "comment": "전반적으로 만족도가 높지만...",
  "recommendation": "괜찮은 선택이지만, 다른 옵션도 고려해보세요.",
  "statistics": {"min_satisfaction": 0.68, "max_satisfaction": 0.70, "avg_satisfaction": 0.69, "variance": 0.02}
}
```

---

### 시나리오 A-7. 취향 지도
요청: `POST /map/taste`  
파일: `app.py`, `domain/a7_taste_map.py`

요청 예시:
```json
{
  "user_text": "감동적인 영화 좋아해요",
  "k": 8
}
```

백엔드 처리 흐름:
1. 텍스트 해시 기반 감정 점수 생성
2. 상위 태그 조합으로 더미 클러스터 생성
3. 해시 기반 2D 좌표 반환

응답 예시(요약):
```json
{
  "clusters": [
    {"cluster_id": 0, "label": "감동적이에요·따뜻해요 분위기", "count": 10}
  ],
  "user_location": {"x": 0.33, "y": 0.71, "nearest_cluster": 0, "cluster_label": "..."}
}
```

---

## 게이미피케이션 / 칵테일 기능 (`/api/*`)

### 시나리오 G-1. 감정 칵테일 생성
요청: `POST /api/cocktail`  
파일: `api/cocktail.py`, `ai/cocktail/*`

핵심 흐름:
1. 입력 검증 → 비율 계산 → Top-N 선택
2. Bedrock LLM 코멘트 생성
3. 이미지 렌더링 후 결과 반환

---

### 시나리오 G-2. 리뷰 작성 → 맛 분석 + 보상
요청: `POST /api/review`  
파일: `api/gamification.py`, `ai/gamification/review.py`

핵심 흐름:
1. 리뷰 길이로 EXP/팝콘 보상
2. LLM 감정 분석 → Flavor 매핑
3. FlavorStat 업데이트

---

### 시나리오 G-3. 홈 상태/밥주기/테마 상점
요청:
- `GET /api/home`
- `POST /api/feeding`
- `GET /api/shop`, `POST /api/shop/buy`, `POST /api/shop/apply`

핵심 흐름:
1. `MovieMong`으로 상태 집계
2. 룰렛 확률로 보상 지급
3. 테마 구매/적용 처리

---

## 추가 메모

- 그룹 추천은 **두 가지 엔드포인트가 존재**합니다.  
  - `/group/simulate` (A-6, app.py)  
  - `/api/group/recommend` (gamification router)  
  목적은 유사하지만 입력 형식이 다릅니다.

- A-1 ~ A-7은 현재 **LLM 호출 없이 deterministic 점수 기반**으로 구현되어 있습니다.  
  (LLM 기반 고정밀 분석은 `ai/analysis/*` 모듈에 구현되어 있음)

---

## DB 저장 구조 (사용자 선호도 / 영화 특성)
아래는 **모델 기준**으로 “어떤 형태로 저장되도록 설계되어 있는지”입니다.  
현재 코드에는 **해당 테이블에 실제로 저장하는 로직이 없습니다**(조회/업데이트 코드 미구현).

### 사용자 선호도 저장 구조
테이블: `user_preferences` (모델: `UserPreference`, `models.py`)
- `user_id`: 사용자 ID (users.id FK)
- `preference_vector_json`: 감정/서사/결말 벡터(JSONB)
- `boost_tags`: 좋아하는 태그 리스트(JSONB)
- `dislike_tags`: 제외/비선호 태그 리스트(JSONB)
- `penalty_tags`: 싫어하는 태그 리스트(JSONB)
- `persona_code`: 페르소나 코드(선택)
- `updated_at`: 갱신 시간

현재 구현 상태:
- A-1 결과는 **응답으로만 반환**되고 DB 저장 없음
- 게이미피케이션 설문(`ai/gamification/survey.py`)은 **DB가 아닌 `user_preferences.json` 파일**에 저장

### 영화 특성 저장 구조
테이블: `movie_vectors` (모델: `MovieVector`, `models.py`)
- `movie_id`: 영화 ID (movies.id FK)
- `emotion_scores`, `narrative_traits`, `direction_mood`, `character_relationship`: 태그 점수(JSONB)
- `ending_preference`: 결말 선호(JSONB)
- `embedding_text`: 임베딩용 텍스트
- `embedding_vector`: 임베딩 벡터(JSONB)
- `updated_at`: 갱신 시간

현재 구현 상태:
- A-2 결과는 **응답으로만 반환**되고 DB 저장 없음
- 실제 영화 메타데이터/태그는 `movies`, `movie_genres`, `movie_tags` 테이블에 저장됨

### 기타 관련 테이블
- `taste_analysis`: 사용자 선호 요약 텍스트 (LLM 생성용, 현재 미사용)
- `reviews`, `review_likes`, `comments`: 리뷰/피드백 데이터
- 게이미피케이션 관련: `users`의 레벨/팝콘 필드 + `flavor_stats`, `theme_inventory`, `question_history`
