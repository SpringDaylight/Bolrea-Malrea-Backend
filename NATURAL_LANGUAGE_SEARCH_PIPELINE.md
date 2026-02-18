# 자연어 검색 파이프라인 (백엔드 기준)

이 문서는 현재 백엔드에서 “자연어 검색”이 어떻게 처리되는지, 어떤 API가 어떤 파일/함수를 호출하고 어떤 입력/출력을 주고받는지 정리합니다.

## 범위
- 대상 API: `POST /search/emotional`
- 구현 위치: `app.py`, `domain/a5_emotional_search.py`, `domain/taxonomy.py`, `utils/validator.py`
- 주의: 이 API는 **실제 검색 결과(영화 리스트)** 가 아니라 **검색엔진에 넘길 쿼리 페이로드**만 반환합니다.

## 엔트리 포인트
1. 클라이언트가 `POST /search/emotional` 호출
2. `app.py`의 `emotional_search_endpoint(body: dict)` 실행

## 요청 입력
`emotional_search_endpoint`는 `body`를 그대로 받아 다음 필드만 사용합니다.
- `text` (string): 자연어 검색 문장
- `genres` (list[string], optional): 장르 필터
- `year_from` (int, optional): 시작 연도
- `year_to` (int, optional): 종료 연도

요청 검증은 `utils/validator.py`의 `validate_request(...)`가 담당하지만, 현재는 JSON 객체인지 여부만 확인합니다. 실제 스키마 파일은 로드되지 않습니다.

## 호출 흐름
1. `app.py: emotional_search_endpoint(body)`
2. `utils/validator.py: validate_request("a5_search_request.json", body)`
3. `domain/a5_emotional_search.py: emotional_search(payload)`
4. `domain/taxonomy.py: load_taxonomy()` 호출로 감정 태그 목록 로드

## 내부 처리 상세
`domain/a5_emotional_search.py`의 핵심 로직은 다음과 같습니다.
1. `text`에서 키워드를 검사하여 감정 태그 점수(`emotion_scores`)를 구성
2. 키워드가 하나도 없으면 기본 점수로 fallback
3. 감정 태그 순서대로 `query_vector`(float 리스트) 생성
4. `genres`, `year_from`, `year_to`로 필터 구성
5. 하이브리드 검색 페이로드 생성 후 반환

### 키워드 매핑 예시
키워드가 `text`에 포함되면 해당 태그 점수가 0.8로 설정됩니다.
- "우울" -> "우울해요"
- "슬프" -> "슬퍼요"
- "긴장" -> "긴장돼요"
- "무서" -> "무서워요"
- "설레" -> "설레요"
- "로맨" -> "로맨틱해요"
- "웃기" -> "웃겨요"
- "밝" -> "밝은 분위기예요"
- "어둡" -> "어두운 분위기예요"
- "잔잔" -> "잔잔해요"
- "현실" -> "현실적이에요"
- "몽환" -> "몽환적이에요"
- "감동" -> "감동적이에요"
- "힐링" -> "힐링돼요"
- "희망" -> "희망적이에요"
- "통쾌" -> "통쾌해요"

### 추가 규칙
- `text`에 "무겁지 않" 또는 "가볍"이 포함되면
  - "밝은 분위기예요" = 0.7
  - "잔잔해요" = 0.6

### 키워드 미탐지 fallback
키워드가 전혀 없으면 아래 기본 점수로 설정됩니다.
- "감동적이에요" = 0.6
- "잔잔해요" = 0.4

## 감정 태그 로딩
`domain/taxonomy.py: load_taxonomy()`는 다음 순서로 태그 목록을 가져옵니다.
1. `ml/data/emotion_tag.json` 파일이 있으면 그 내용을 사용
2. 없으면 내부 기본 태그 목록을 사용

## 출력 (반환 결과)
`POST /search/emotional`의 응답은 검색엔진(예: OpenSearch)에 넘길 쿼리 페이로드입니다.

```json
{
  "intent": "search",
  "expanded_query": {
    "emotion_scores": {
      "감동적이에요": 0.6,
      "잔잔해요": 0.4
    }
  },
  "hybrid_query": {
    "query": {
      "bool": {
        "must": [],
        "filter": [
          { "terms": { "genres": ["Drama", "Romance"] } },
          { "range": { "release_year": { "gte": 2010, "lte": 2020 } } }
        ]
      }
    },
    "knn": {
      "field": "emotion_vector",
      "query_vector": [0.0, 0.6, 0.4, 0.0],
      "k": 50,
      "num_candidates": 200
    }
  }
}
```

## 현재 미구현/주의 사항
- 실제 검색 실행(예: OpenSearch 쿼리) 및 결과 반환은 구현되어 있지 않습니다.
- `services/vector_store.py`는 스텁이므로 검색 결과를 생성하지 않습니다.
- `a5_search_request.json` 스키마 파일은 참조만 되고 실제 로드/검증은 하지 않습니다.

## 참고: 다른 검색 경로
홈 화면이 “자연어 감성 검색”이 아니라 단순 텍스트 검색이라면,
`GET /api/movies?query=...` 경로가 사용되며,
`api/movies.py:get_movies` -> `repositories/movie.py:search`로 DB 검색이 수행됩니다.
