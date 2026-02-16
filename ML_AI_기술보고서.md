# Backend ML/AI 기능 기술 보고서

## 📋 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [AI 모듈 (ai/)](#ai-모듈)
4. [ML 모듈 (ml/)](#ml-모듈)
5. [통합 구조 (domain/)](#통합-구조)
6. [API 엔드포인트](#api-엔드포인트)
7. [데이터 플로우](#데이터-플로우)
8. [기술 스택](#기술-스택)

---

## 개요

Bolrea-Malrea Backend는 **정서·서사 기반 영화 추천 시스템**을 핵심으로 하며, 다음 3가지 주요 AI/ML 기능을 제공합니다:

### 핵심 기능
1. **영화 추천 시스템 (A-1 ~ A-7)** - 정서/서사 기반 개인화 추천
2. **게이미피케이션 (리뷰몽)** - 캐릭터 육성 및 리뷰 분석
3. **감정 칵테일 생성기** - 감정 분석 기반 시각화

### 기술적 특징
- **AWS Bedrock** 기반 LLM 통합 (Claude 3 Haiku)
- **Titan Embedding v2** 벡터화
- **코사인 유사도** 기반 매칭
- **부정어 처리** 시스템 (LLM + Rule-based Fallback)
- **그룹 추천** (Least Misery Strategy)

---

## 아키텍처

```
Backend/
├── ai/                    # AI 기능 (LLM 기반)
│   ├── analysis/         # 영화 분석 모듈
│   ├── cocktail/         # 감정 칵테일 생성기
│   ├── gamification/     # 리뷰몽 게이미피케이션
│   ├── llm_client.py     # Bedrock 클라이언트
│   └── llm_executor.py   # LLM 실행 엔진
│
├── ml/                    # ML 모델 및 데이터
│   ├── data/             # 택소노미, 영화 데이터셋
│   └── model_sample/     # 분석 모듈 (A-1~A-7)
│
├── domain/               # 비즈니스 로직 통합
│   ├── a1_preference.py  # 사용자 취향 분석
│   ├── a2_movie_vector.py # 영화 벡터화
│   ├── a3_prediction.py  # 만족 확률 계산
│   ├── a4_explanation.py # 설명 생성
│   ├── a5_emotional_search.py # 감성 검색
│   ├── a6_group_simulation.py # 그룹 추천
│   └── a7_taste_map.py   # 취향 지도
│
├── api/                  # FastAPI 엔드포인트
│   ├── movies.py         # 영화 API
│   ├── reviews.py        # 리뷰 API
│   ├── cocktail.py       # 칵테일 API
│   └── gamification.py   # 게이미피케이션 API
│
└── app.py               # FastAPI 메인 앱
```

---

## AI 모듈 (ai/)

### 1. 영화 분석 모듈 (ai/analysis/)

#### 핵심 파일 구조
```
analysis/
├── sentiment.py          # A-1: 사용자 취향 분석
├── embedding.py          # A-2: 영화 벡터화
├── similarity.py         # A-3: 만족 확률 계산
├── description.py        # A-4: 설명 생성
├── group_recommendation.py # A-6: 그룹 추천
├── clustering.py         # A-7: 취향 지도
├── vector_db.py          # 벡터 DB 유틸
└── README.md
```

#### A-1: 사용자 취향 분석 (sentiment.py)

**목적**: 사용자 입력 텍스트를 분석하여 정서·서사 기반 취향 벡터 생성

**주요 기능**:

1. **LLM 기반 취향 분석** (`analyze_user_preference_with_llm`)
   - Claude 3 Haiku 사용
   - 80개 태그 (감정 20 + 서사 20 + 연출 20 + 캐릭터 20)에 대한 점수 부여
   - 문맥 이해를 통한 정교한 분석

2. **부정어 처리 시스템** (`extract_negative_filters_with_llm`)
   - 문제: "무서운 거 싫어" → 키워드 매칭 → "무서운" 감지 → 공포 영화 추천 (잘못됨)
   - 해결: LLM으로 부정 의도 파악 → exclude_tags에 추가 → 필터링
   - Fallback: 규칙 기반 부정어 검출 (`detect_negation_fallback`)

3. **영화 선택 기반 취향 추출**
   - 좋아하는/싫어하는 영화에서 태그 자동 추출
   - 빈도 기반 필터링 (노이즈 제거)

**입력 예시**:
```python
{
  "text": "무서운 거 싫어. 로맨스 좋아해요",
  "dislikes": "공포 영화 제외"
}
```

**출력 예시**:
```python
{
  "emotion_scores": {
    "로맨틱해요": 0.85,
    "설레요": 0.72,
    "무서워요": 0.15  # 낮은 점수
  },
  "exclude_genres": ["Horror"],
  "exclude_tags": ["무서워요", "피가 튀어"],
  "method_used": "llm"
}
```

---

#### A-2: 영화 벡터화 (embedding.py)

**목적**: 영화 메타데이터를 분석하여 정서·서사 기반 특성 벡터 생성

**주요 기능**:

1. **LLM 기반 영화 분석** (`analyze_with_llm`)
   - 영화 정보 (제목, 줄거리, 장르, 키워드) 분석
   - 4개 차원 분석:
     - emotion (감정)
     - story_flow (서사 흐름)
     - direction_mood (연출/분위기)
     - character_relationship (캐릭터/관계)
   - 각 태그별 0.0~1.0 점수 부여

2. **임베딩 벡터 생성** (`embedding_vector`)
   - AWS Bedrock Titan Embedding v2 사용
   - 1024차원 벡터 생성
   - 정규화 (normalize=True)

3. **Fallback 모드**
   - LLM 실패 시 Deterministic 점수 생성 (`stable_score`)
   - 해시 기반 안정적인 점수 생성

**프로세스**:
```
영화 메타데이터 → LLM 분석 → 태그 점수 → 임베딩 텍스트 생성 → Titan 벡터화
```

**출력 예시**:
```python
{
  "movie_id": 123,
  "title": "인생은 아름다워",
  "emotion_scores": {
    "감동적이에요": 0.92,
    "따뜻해요": 0.88,
    "슬퍼요": 0.65
  },
  "narrative_traits": {
    "기승전결이 뚜렷해요": 0.85
  },
  "embedding": [0.123, -0.456, ...],  # 1024차원
  "embedding_text": "Title: 인생은 아름다워. Emotions: 감동적이에요, 따뜻해요, 슬퍼요"
}
```

---

#### A-3: 만족 확률 계산 (similarity.py)

**목적**: 사용자 취향과 영화 특성 간 만족 확률 계산

**주요 알고리즘**:

1. **코사인 유사도 계산** (`cosine_sim`)
   - 차원별 유사도: emotion, narrative, ending
   - 범위: -1.0 (정반대) ~ 1.0 (완전 일치)

2. **Boost/Penalty 메커니즘**
   - Boost: 좋아하는 태그 보너스 (`_calculate_boost_score`)
   - Penalty: 싫어하는 태그 페널티 (`_calculate_dislike_penalty`)
   - 모든 카테고리 (감정, 서사, 연출, 캐릭터)에서 체크

3. **최종 점수 계산**
   ```python
   raw_score = (w_e * sim_e + w_n * sim_n + w_d * sim_d) 
               + (boost_weight * boost_score) 
               - (penalty_weight * dislike_penalty)
   
   probability = (raw_score + 1) / 2  # -1~1 → 0~1 변환
   ```

4. **신뢰도 계산**
   - 차원 간 일관성 측정 (표준편차 기반)
   - 분산이 낮을수록 신뢰도 높음

**출력 예시**:
```python
{
  "probability": 0.85,      # 만족 확률 (0~1)
  "confidence": 0.92,       # 신뢰도 (0~1)
  "raw_score": 0.74,        # 원본 점수 (-1~1)
  "breakdown": {
    "emotion_similarity": 0.91,
    "narrative_similarity": 0.85,
    "ending_similarity": 0.78,
    "boost_score": 0.12,
    "dislike_penalty": 0.05,
    "top_factors": ["정서 톤", "서사 초점"]
  }
}
```

---

#### A-6: 그룹 추천 (group_recommendation.py)

**목적**: 여러 사용자의 취향을 종합하여 그룹 만족도 계산

**전략**:

- **Least Misery Strategy**: 가장 불만족한 멤버의 점수를 그룹 점수로 사용
- 모든 멤버가 최소한의 만족도를 보장

**프로세스**:
```
각 멤버 취향 분석 → 영화와 매칭 → 멤버별 만족도 계산 → 최소값 선택
```

**출력 예시**:
```python
{
  "group_score": 0.72,
  "strategy": "least_misery",
  "members": [
    {"user_id": "user1", "probability": 0.85, "level": "만족"},
    {"user_id": "user2", "probability": 0.72, "level": "만족"}
  ],
  "statistics": {
    "min_satisfaction": 0.72,
    "max_satisfaction": 0.85,
    "avg_satisfaction": 0.785,
    "variance": 0.0085
  }
}
```

---

### 2. 게이미피케이션 (ai/gamification/)

#### 구조
```
gamification/
├── core.py              # 핵심 로직 (레벨, 경험치, 팝콘)
├── review.py            # 리뷰 분석 및 보상
├── survey.py            # 초기 설문 처리
├── feeding.py           # 밥주기 시스템
├── question.py          # 일일 질문
├── theme.py             # 테마 관리
└── survey_questions.json # 설문 데이터
```

#### 핵심 기능

**1. 캐릭터 성장 시스템 (core.py)**

- **레벨 시스템**: Lv.1 (알) → Lv.30 (최종 진화)
- **성장 단계**:
  - Lv.1: Egg (알)
  - Lv.2-5: Toddler (유아기)
  - Lv.6-14: Child (아동기)
  - Lv.15-25: Teen (청소년기)
  - Lv.26-30: Adult (성체)

- **경험치 테이블**:
  ```python
  LEVEL_TABLE = {
      1: 0,
      2: 50,      # 유아기 진입
      5: 500,     # 1차 진화
      10: 3000,   # 2차 진화
      20: 13500,  # 3차 진화
      30: 30000   # 최종 진화
  }
  ```

**2. 리뷰 분석 및 보상 (review.py)**

- **LLM 기반 맛 분석** (`_analyze_flavor_with_llm`)
  - 리뷰 텍스트 → 8가지 맛 분류
  - Sweet (달콤), Spicy (매운), Onion (어니언), Cheese (치즈)
  - Dark (초코), Salty (소금), Mint (민트), Original (오리지널)

- **보상 시스템**:
  - 간단 리뷰 (< 50자): EXP +5, 팝콘 +3
  - 상세 리뷰 (≥ 50자): EXP +30, 팝콘 +12

- **맛 스탯 업데이트**:
  - 각 맛별 점수 누적
  - 메인 맛 결정 (가장 높은 점수)

**3. 초기 설문 (survey.py)**

- 사용자 취향 프로필 생성
- Boost/Penalty 태그 추출
- 가중치 설정
- `user_preferences.json`에 저장

---

### 3. 감정 칵테일 생성기 (ai/cocktail/)

#### 구조
```
cocktail/
├── emotion_cocktail_generator.py  # 메인 파이프라인
├── analyzers.py                   # 분석 컴포넌트
├── models.py                      # 데이터 모델
├── validators.py                  # 입력 검증
└── image_renderer.py              # 이미지 렌더링
```

#### 파이프라인 (7단계)

**1. 입력 검증** (validators.py)

- 7가지 맛 값 검증 (sweet, spicy, onion, cheese, dark, salty, mint)
- 0 이상 정수 확인
- 정규화 (음수 → 0)

**2. 비율 계산** (analyzers.py - TasteAnalyzer)
- 각 맛의 비율 계산 (0.0 ~ 1.0)
- 맛-감정-색상 매핑:
  ```python
  TASTE_EMOTION_COLOR_MAP = {
      'sweet': ('설렘, 행복', '#FFB7C5'),
      'spicy': ('분노, 긴장', '#FF4500'),
      'onion': ('호기심, 추리', '#E0FFFF'),
      'cheese': ('즐거움, 활기', '#FFD700'),
      'dark': ('우울, 진지', '#4B0082'),
      'salty': ('슬픔, 감동', '#87CEEB'),
      'mint': ('신비, 경이', '#98FF98')
  }
  ```

**3. Top-N 선정** (analyzers.py - TopNSelector)
- 5% 이상 비율을 가진 맛만 필터링
- 비율 높은 순으로 정렬
- 최대 3개 선정

**4. 이미지 생성** (analyzers.py - CocktailImageGenerator)
- 베이스 이미지 선택
- 비율 기반 세로 그라데이션 생성
- 1개: 단색, 2개: 2색, 3개: 3색

**5. 성분표 생성** (analyzers.py - IngredientLabelGenerator)
- "감정명 비율% + 감정명 비율% + ..." 형식
- 예: "설렘, 행복 70% + 우울, 진지 30%"

**6. LLM 코멘트 생성** (analyzers.py - LLMCommentGenerator)
- Claude 3 Haiku 사용
- 영화적인 칵테일 이름 생성
- 2줄 이내 위로 메시지
- Fallback: 기본값 반환

**7. 최종 출력 조립** (analyzers.py - CocktailOutputAssembler)
- 모든 정보 통합
- CocktailOutput 객체 생성

---

### 4. LLM 클라이언트 (ai/llm_client.py)

**BedrockClient 클래스**:

- AWS Bedrock Runtime 클라이언트 래퍼
- 환경 변수 기반 설정:
  ```python
  AWS_REGION=ap-northeast-2
  BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
  BEDROCK_MAX_TOKENS=1024
  BEDROCK_TEMPERATURE=0.2
  ```
- 재시도 로직 (retry=2)
- 타임아웃 처리

---

## ML 모듈 (ml/)

### 데이터 (ml/data/)

#### 1. emotion_tag.json - 정서 택소노미

**80개 태그 구조**:
```json
{
  "emotion": {
    "tags": [
      "감동적이에요", "무서워요", "슬퍼요", "웃겨요", 
      "로맨틱해요", "긴장돼요", "통쾌해요", "우울해요",
      "따뜻해요", "소름 돋아요", "여운이 길어요", "힐링돼요",
      "설레요", "피가 튀어", "현실적이에요", "몽환적이에요",
      "어두운 분위기예요", "밝은 분위기예요", "잔인해요", "순수해요"
    ]
  },
  "story_flow": {
    "tags": [
      "반전이 많아요", "전개가 빨라요", "기승전결이 뚜렷해요",
      "복선이 많아요", "느린 전개예요", "예측 가능해요",
      "복잡해요", "단순해요", "다층적이에요", "선형적이에요",
      ...
    ]
  },
  "direction_mood": {
    "tags": [
      "영상미가 뛰어나요", "음악이 좋아요", "연출이 독특해요",
      ...
    ]
  },
  "character_relationship": {
    "tags": [
      "캐릭터가 매력적이에요", "관계가 복잡해요", "성장하는 캐릭터예요",
      ...
    ]
  }
}
```

#### 2. movies_dataset_final.json - 영화 데이터셋

**TMDB 기반 영화 정보**:

```json
{
  "id": 123,
  "title": "인생은 아름다워",
  "overview": "2차 세계대전 중...",
  "genres": ["드라마", "코미디", "전쟁"],
  "keywords": ["전쟁", "가족", "희망"],
  "directors": ["로베르토 베니니"],
  "cast": ["로베르토 베니니", "니콜레타 브라스키"],
  "release_date": "1997-12-20",
  "runtime": 116,
  "vote_average": 8.5,
  "vote_count": 12345
}
```

---

## 통합 구조 (domain/)

Backend의 `domain/` 폴더는 ML 모듈을 FastAPI와 통합하는 비즈니스 로직 레이어입니다.

### 파일 구조

```
domain/
├── a1_preference.py       # A-1 통합
├── a2_movie_vector.py     # A-2 통합
├── a3_prediction.py       # A-3 통합
├── a4_explanation.py      # A-4 통합
├── a5_emotional_search.py # A-5 통합
├── a6_group_simulation.py # A-6 통합
├── a7_taste_map.py        # A-7 통합
└── taxonomy.py            # 택소노미 로더
```

### 역할

1. **ML 모듈 임포트**:
   ```python
   from ai.analysis import sentiment, embedding, similarity
   ```

2. **FastAPI 스키마 변환**:
   ```python
   # Pydantic 모델 → ML 입력 형식
   # ML 출력 → Pydantic 응답 모델
   ```

3. **에러 처리 및 로깅**

4. **비즈니스 로직 추가**:
   - 사용자 인증
   - 데이터 검증
   - 캐싱
   - 로깅

---

## API 엔드포인트

### 1. 영화 추천 API (api/movies.py)

**A-1: 사용자 취향 분석**
```http
POST /analyze/preference
Content-Type: application/json

{
  "text": "감동적이고 따뜻한 영화 좋아해요",
  "dislikes": "무서운 거 싫어"
}
```

**A-2: 영화 벡터화**
```http
POST /movie/vector
Content-Type: application/json

{
  "movie_id": 123,
  "title": "인생은 아름다워",
  "overview": "...",
  "genres": ["드라마"]
}
```

**A-3: 만족 확률 계산**
```http
POST /predict/satisfaction
Content-Type: application/json

{
  "user_profile": {...},
  "movie_profile": {...},
  "dislike_tags": [],
  "boost_tags": []
}
```

**A-5: 감성 검색**
```http
POST /search/emotional
Content-Type: application/json

{
  "text": "우울한데 너무 무겁지 않은 영화",
  "genres": ["드라마"],
  "year_from": 2010
}
```

**A-6: 그룹 추천**
```http
POST /group/simulate
Content-Type: application/json

{
  "members": [
    {"user_id": "user1", "profile": {...}},
    {"user_id": "user2", "profile": {...}}
  ],
  "movie_profile": {...}
}
```

**A-7: 취향 지도**
```http
POST /map/taste
Content-Type: application/json

{
  "user_text": "감동적인 영화 좋아해요",
  "k": 8
}
```

---

### 2. 게이미피케이션 API (api/gamification.py)

**리뷰 작성**
```http
POST /gamification/review
Content-Type: application/json

{
  "user_id": "user123",
  "review_text": "정말 감동적인 영화였어요!",
  "is_detailed": true
}
```

**캐릭터 상태 조회**
```http
GET /gamification/status?user_id=user123
```

**밥주기**
```http
POST /gamification/feed
Content-Type: application/json

{
  "user_id": "user123"
}
```

---

### 3. 칵테일 API (api/cocktail.py)

**칵테일 생성**
```http
POST /cocktail/generate
Content-Type: application/json

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

**응답 예시**:
```json
{
  "cocktail_name": "감정의 칵테일",
  "comfort_message": "오늘 하루도 수고하셨어요...",
  "base_image_id": "static/배경제거W.png",
  "gradient_info": {
    "direction": "vertical",
    "colors": ["#FFB7C5", "#4B0082"],
    "stops": [0.7, 1.0]
  },
  "ingredient_label": "설렘, 행복 70% + 우울, 진지 30%"
}
```

---

## 데이터 플로우

### 영화 추천 플로우

```
1. 사용자 입력
   ↓
2. A-1: 취향 분석 (LLM)
   - 텍스트 → 정서 벡터
   - 부정어 처리
   ↓
3. A-2: 영화 벡터화 (LLM + Titan)
   - 영화 메타데이터 → 정서 벡터
   - 임베딩 생성
   ↓
4. A-3: 만족 확률 계산
   - 코사인 유사도
   - Boost/Penalty
   ↓
5. A-4: 설명 생성 (LLM)
   - 자연어 설명
   ↓
6. 추천 결과 반환
```

### 게이미피케이션 플로우

```
1. 리뷰 작성
   ↓
2. LLM 맛 분석
   - 리뷰 텍스트 → 8가지 맛
   ↓
3. 보상 지급
   - EXP, 팝콘
   ↓
4. 맛 스탯 업데이트
   ↓
5. 레벨업 체크
   - 성장 단계 변경
   ↓
6. 캐릭터 이미지 업데이트
```

---

## 기술 스택

### AI/ML
- **AWS Bedrock**
  - Claude 3 Haiku (LLM)
  - Titan Embedding v2 (벡터화)
- **Numpy** - 벡터 연산
- **Scikit-learn** - 클러스터링 (UMAP, K-Means)

### Backend
- **FastAPI** - REST API 프레임워크
- **SQLAlchemy** - ORM
- **Pydantic** - 데이터 검증
- **Alembic** - DB 마이그레이션

### 데이터베이스
- **PostgreSQL** - 메인 DB
- **SQLite** - 게이미피케이션 (로컬)

### 배포
- **Docker** - 컨테이너화
- **Jenkins** - CI/CD
- **AWS ECS** - 컨테이너 오케스트레이션

---

## 테스트

### 통합 테스트 (test_ml_integration.py)

전체 ML 파이프라인 테스트:
```bash
python test_ml_integration.py
```

**테스트 항목**:
- A-1: 사용자 취향 분석
- A-2: 영화 벡터화
- A-3: 만족 확률 계산
- A-4: 설명 생성
- A-5: 감성 검색
- A-6: 그룹 추천
- A-7: 취향 지도

### 리뷰 API 테스트 (test_review_api.py)

리뷰 CRUD 및 게이미피케이션 테스트:
```bash
python test_review_api.py
```

---

## 주요 특징 및 장점

### 1. 정서·서사 기반 추천
- 단순 장르 매칭을 넘어선 감정 기반 추천
- 80개 세분화된 태그로 정교한 분석

### 2. 부정어 처리
- LLM 기반 의도 파악
- "무서운 거 싫어" → 공포 영화 제외
- Fallback 시스템으로 안정성 보장

### 3. 그룹 추천
- Least Misery Strategy
- 모든 멤버의 최소 만족도 보장

### 4. 게이미피케이션
- 리뷰 작성 동기 부여
- 캐릭터 육성 시스템
- 맛 스탯 기반 개성화

### 5. 확장성
- 모듈화된 구조
- ML 모듈 독립 실행 가능
- API 레이어 분리

---

## 개선 가능 영역

### 1. 성능 최적화
- LLM 호출 캐싱
- 벡터 DB 도입 (Pinecone, Weaviate)
- 배치 처리

### 2. 정확도 향상
- Fine-tuning (영화 도메인)
- 더 많은 학습 데이터
- A/B 테스트

### 3. 기능 확장
- 실시간 추천
- 협업 필터링 통합
- 시계열 분석 (취향 변화)

---

## 결론

Bolrea-Malrea Backend의 ML/AI 시스템은 **정서·서사 기반 영화 추천**을 핵심으로, **게이미피케이션**과 **감정 시각화**를 통합한 종합 플랫폼입니다.

**핵심 강점**:
- AWS Bedrock 기반 LLM 통합
- 부정어 처리 시스템
- 그룹 추천 알고리즘
- 모듈화된 아키텍처

**향후 방향**:
- 성능 최적화 (캐싱, 벡터 DB)
- 정확도 향상 (Fine-tuning)
- 기능 확장 (실시간 추천, 협업 필터링)

---

**작성일**: 2026-02-15  
**버전**: 1.0  
**작성자**: Kiro AI Assistant
