# 리뷰 장르별 업데이트 수정 완료

## 📋 요약

사용자가 애니메이션 영화에 리뷰를 작성했지만 `review.genres`가 비어있던 문제를 해결했습니다.

## 🐛 문제 원인

`api/reviews.py`에서 영화 장르를 가져올 때 잘못된 필드를 참조했습니다:

```python
# ❌ 잘못된 코드
movie = MovieRepository(db).get_by_id(db_review.movie_id)
genre = movie.genre if movie else None  # movie.genre는 존재하지 않음
```

Movie 모델은 `genre` 필드가 아닌 `genres` 관계를 가집니다:
- `movie.genres`: MovieGenre 객체들의 리스트
- 각 MovieGenre 객체는 `.genre` 속성을 가짐

## ✅ 해결 방법

영화 장르를 올바르게 가져오도록 수정했습니다:

```python
# ✅ 수정된 코드
movie = MovieRepository(db).get_with_details(db_review.movie_id)
genre = movie.genres[0].genre if movie and movie.genres else None
```

## 📝 수정된 파일

- `Bolrea-Malrea-Backend/api/reviews.py`
  - `create_review()` 함수 (2곳)
  - `update_review()` 함수 (2곳)

## 🧪 테스트 결과

### 수정 전
```json
{
  "review": {
    "review_count": 0,
    "genres": {},
    "global": {...}
  }
}
```

### 수정 후
```json
{
  "review": {
    "review_count": 1,
    "genres": {
      "애니메이션": {
        "emotion_scores": {
          "감동적이에요": 0.191,
          "따뜻해요": 0.718,
          "힐링돼요": 0.718,
          ...
        },
        "narrative_traits": {...},
        "ending_preference": {...},
        "direction_mood": {...},
        "character_relationship": {...}
      }
    },
    "global": {...},
    "last_updated": "2026-02-27T07:49:19.420969Z"
  }
}
```

## 🔧 기존 데이터 복구

기존에 작성된 리뷰의 선호도 데이터를 복구하려면:

```bash
cd Bolrea-Malrea-Backend
python test_manual_review_update.py
```

이 스크립트는:
1. 사용자의 기존 리뷰를 분석
2. 영화 장르를 올바르게 가져옴
3. `review.genres`에 장르별 데이터 저장
4. `review_count` 증가
5. `global` 재계산

## 📊 검증 스크립트

### 1. 현재 상태 확인
```bash
python test_review_genre_update.py
```

출력:
- 현재 review_count
- 저장된 genres 목록
- 장르별 데이터 샘플
- 문제 진단

### 2. 전체 플로우 테스트
```bash
python test_complete_flow.py
```

출력:
- 데이터 구조 확인
- baseline, review, global 상태
- 추천 시나리오 테스트 (장르 유/무)
- 전체 시스템 정상 작동 여부

### 3. 신규 리뷰 시뮬레이션
```bash
python test_new_review_simulation.py
```

출력:
- 새 리뷰 작성 시 동작 과정
- 장르별 데이터 업데이트
- global 재계산
- 추천 시나리오별 동작

## 🎯 향후 동작

이제 새로운 리뷰가 작성되면:

1. **리뷰 내용 분석**: A-1 API로 선호도 분석
2. **장르 추출**: 영화의 첫 번째 장르 사용
3. **장르별 저장**: `review.genres[장르]`에 분석 결과 저장
4. **전체 누적**: `review.global`에 누적 평균 저장
5. **카운트 증가**: `review_count` 증가
6. **최종 계산**: `global = baseline * 0.3 + review.global * 0.7`

## 📖 추천 시나리오

### 시나리오 1: 장르 명시 없음
```
사용자: "따뜻한 영화 추천해줘"
→ global 사용 (baseline 30% + review.global 70%)
```

### 시나리오 2: 장르 명시 (리뷰 있음)
```
사용자: "재미있는 애니메이션 추천해줘"
→ baseline + review.genres['애니메이션'] 사용
```

### 시나리오 3: 장르 명시 (리뷰 없음)
```
사용자: "재미있는 드라마 추천해줘"
→ global 사용 (해당 장르 리뷰 없음)
```

## ✅ 검증 완료

- ✅ 영화 장르 올바르게 가져오기
- ✅ review.genres에 장르별 데이터 저장
- ✅ review_count 증가
- ✅ global 재계산
- ✅ 장르별 추천 동작
- ✅ 전체 플로우 정상 작동
- ✅ 기존 데이터 복구 가능

## 📚 관련 문서

- `PREFERENCE_SYSTEM_GUIDE.md`: 전체 시스템 가이드
- `REVIEW_GENRE_FIX.md`: 상세 수정 내역
- `utils/preference_helper.py`: 헬퍼 함수
- `api/reviews.py`: 리뷰 API

## 🚀 다음 단계

로컬에서 테스트하려면:

1. 백엔드 서버 시작:
```bash
cd Bolrea-Malrea-Backend
python app.py
```

2. 프론트엔드에서 리뷰 작성:
- 영화 상세 페이지에서 리뷰 작성
- 자동으로 선호도 업데이트됨

3. 확인:
```bash
python check_db_detail.py user_7a351b0ba78840e5b35c72ae2d551724
```

## 📅 날짜

2024-02-27

---

**수정 완료!** 이제 리뷰를 작성하면 장르별 선호도가 정상적으로 업데이트됩니다. 🎉
