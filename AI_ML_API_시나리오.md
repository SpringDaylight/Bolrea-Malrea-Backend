# 프론트 → 백엔드 AI/ML API 시나리오

이 문서는 프론트엔드가 API를 호출했을 때, **실제로 어떤 AI/ML 로직이 수행되고 어떤 응답이 오는지**를 시나리오별로 정리합니다.  
현재 코드에 **실제로 연결된 엔드포인트 기준**으로 작성하고, 마지막에 **미연결(설계만 있는) 파이프라인**도 참고로 정리했습니다.

## 현재 구현된 시나리오

### 시나리오 1. 감정 칵테일 생성
요청: `POST /api/cocktail`  
파일: `api/cocktail.py`, `ai/cocktail/*`

요청 예시:
```json
{
  "sweet": 70,
  "spicy": 10,
  "onion": 5,
  "cheese": 5,
  "dark": 30,
  "salty": 20,
  "mint": 10
}
```

백엔드 처리 흐름:
1. `api/cocktail.py`에서 요청 수신
2. `EmotionCocktailGenerator.generate()` 실행  
3. `ai/cocktail/validators.py`로 입력 검증  
4. `ai/cocktail/analyzers.py`에서 맛 비율 계산 → Top-N 선택 → 라벨 생성  
5. `ai/cocktail/analyzers.py`의 `LLMCommentGenerator`가 Bedrock으로 칵테일 이름/메시지 생성  
6. `ai/cocktail/image_renderer.py`로 그라데이션 이미지 렌더링  

응답 예시:
```json
{
  "success": true,
  "data": {
    "image_url": "/static/output/cocktail_감정의_칵테일.png",
    "ingredient_label": "설렘, 행복 70% + 우울, 진지 30%",
    "cocktail_name": "감정의 칵테일",
    "comfort_message": "오늘 하루도 수고하셨어요...",
    "gradient_colors": ["#FFB7C5", "#4B0082"]
  }
}
```

메모:
- Bedrock 호출 실패 시 기본 코멘트로 fallback 됩니다.  
- `BEDROCK_REGION`, `BEDROCK_MODEL_ID` 환경 변수 필요.  

---

### 시나리오 2. 리뷰 작성 → 맛 분석 + 보상
요청: `POST /api/review`  
파일: `api/gamification.py`, `ai/gamification/review.py`, `ai/analysis/sentiment.py`

요청 예시:
```json
{
  "review": "정말 감동적이고 따뜻한 영화였어요."
}
```

백엔드 처리 흐름:
1. `MovieMong(DEMO_USER_ID)` 인스턴스 생성  
2. 리뷰 길이로 보상 결정 (간단/상세)  
3. `ai/analysis/sentiment.analyze_user_preference_with_llm`로 감정 태그 분석  
4. 감정 태그 → FLAVOR 매핑 후 사용자 FlavorStat 업데이트  

응답 예시:
```json
{
  "success": true,
  "reward": {"type": "simple", "exp": 5, "popcorn": 3},
  "analysis": {
    "flavor": "Sweet",
    "flavor_name": "달콤",
    "main_flavor": "Sweet",
    "main_flavor_name": "달콤"
  },
  "message": "달콤 팝콘 획득! (EXP +5, 팝콘 +3)"
}
```

메모:
- LLM 실패 시 키워드 기반 fallback 사용  
- 현재는 `DEMO_USER_ID = "user_demo"` 고정

---

### 시나리오 3. 홈 화면 조회 (게이미피케이션 상태)
요청: `GET /api/home`  
파일: `api/gamification.py`, `ai/gamification/__init__.py`, `ai/gamification/core.py`

백엔드 처리 흐름:
1. `MovieMong.get_home_data()` 호출  
2. 사용자 레벨/경험치/팝콘/이미지/오늘의 질문 상태 조립  

응답 예시(요약):
```json
{
  "user_id": "user_demo",
  "character": {
    "level": 1,
    "stage": "Egg",
    "exp": 0,
    "flavor": "Sweet",
    "image_path": "리뷰몽_1차.png"
  },
  "currency": {"popcorn": 0},
  "daily_status": {"can_answer_question": true, "today_question": "..."}
}
```

---

### 시나리오 4. 밥주기 룰렛
요청: `POST /api/feeding`  
파일: `api/gamification.py`, `ai/gamification/feeding.py`

백엔드 처리 흐름:
1. `ProbabilityEngine` 확률로 상품 선정  
2. EXP/팝콘 보상 지급  
3. 마지막 밥준 날짜 기록  

응답 예시(요약):
```json
{
  "success": true,
  "prize": "핫도그",
  "target_angle": 108,
  "message": "든든한 핫도그 당첨! (Good)",
  "reward": {"exp": 40, "popcorn": 15}
}
```

---

### 시나리오 5. 그룹 추천
요청: `POST /api/group/recommend`  
파일: `api/gamification.py`, `ai/analysis/group_recommendation.py`, `ai/analysis/embedding.py`, `ai/analysis/similarity.py`

요청 예시:
```json
{
  "users": [
    {"name": "A", "text": "감동적인 영화 좋아해요"},
    {"name": "B", "text": "반전 많은 영화 좋아해요"}
  ],
  "target_movie_id": 123
}
```

백엔드 처리 흐름:
1. 서버 시작 시 `TAXONOMY`, `GROUPED_MOVIES` 로드  
2. 사용자 텍스트 → 간이 프로필 생성  
3. 대상 영화 프로필 생성 → 사용자별 만족 확률 계산  
4. 그룹 점수는 평균값 사용  

응답 예시(요약):
```json
{
  "success": true,
  "data": {
    "movie_title": "인생은 아름다워",
    "group_probability": 0.72,
    "user_details": [
      {"name": "A", "probability": 0.80, "level": "만족"},
      {"name": "B", "probability": 0.64, "level": "보통"}
    ]
  }
}
```

메모:
- `data/movies_dataset_final.json`, `data/emotion_tag.json` 경로가 필요합니다.  
  현재 리포에 `ml/data/*`만 존재하면 경로 조정이 필요합니다.

---

### 시나리오 6. 테마 상점/적용 (게이미피케이션)
요청:  
`GET /api/shop`  
`POST /api/shop/buy`  
`POST /api/shop/apply`  

파일: `api/gamification.py`, `ai/gamification/theme.py`

백엔드 처리 흐름:
1. 보유 테마 조회 및 상태 반환  
2. 팝콘 잔액 확인 후 구매 처리  
3. 적용 테마 업데이트  

---

## 설계상 존재하지만 API 미연결인 시나리오 (참고)

아래 파이프라인은 `domain/*`에 구현돼 있으나, 현재 FastAPI 라우터에는 연결되어 있지 않습니다.  
필요 시 신규 라우터로 연결하면 프론트에서 직접 호출 가능해집니다.

### A-1 사용자 취향 분석
파일: `domain/a1_preference.py`  
기능: 사용자 텍스트 → 취향 벡터 + 부정어 처리

### A-2 영화 벡터화
파일: `domain/a2_movie_vector.py`  
기능: 영화 메타데이터 → 정서/서사/연출/캐릭터 점수화

### A-3 만족 확률 계산
파일: `domain/a3_prediction.py`  
기능: 사용자 프로필 vs 영화 프로필 매칭 확률

### A-4 설명 생성
파일: `domain/a4_explanation.py`  
기능: A-3 결과를 자연어 설명으로 변환

### A-5 감성 검색
파일: `domain/a5_emotional_search.py`  
기능: 감정 키워드 확장 + 하이브리드 검색 쿼리 생성

### A-7 취향 지도
파일: `domain/a7_taste_map.py`  
기능: 텍스트 기반 취향 지도(더미 클러스터) 생성

---

## 다음 단계 제안
1. 위 “미연결 시나리오”에 대한 API 라우터 추가
2. `data/` 경로 정리 (현재 `ml/data`와 불일치)
3. 실제 프론트 요청/응답 예시를 스웨거(OpenAPI)와 일치시키기
