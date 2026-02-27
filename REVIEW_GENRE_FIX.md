# Review Genre Update Fix

## 문제 상황
사용자가 애니메이션 장르 영화에 대한 리뷰를 작성했지만, `review.genres`가 비어있고 `review_count`가 0으로 남아있었습니다.

## 원인
`api/reviews.py`에서 영화 장르를 가져올 때 잘못된 코드를 사용했습니다:

```python
# 잘못된 코드
movie = MovieRepository(db).get_by_id(db_review.movie_id)
genre = movie.genre if movie else None  # ❌ movie.genre는 존재하지 않음
```

Movie 모델은 `genre` 필드가 아닌 `genres` 관계(relationship)를 가지고 있습니다:
- `movie.genres`: MovieGenre 객체들의 리스트
- 각 MovieGenre 객체는 `.genre` 속성을 가짐

## 해결 방법
영화 장르를 올바르게 가져오도록 수정했습니다:

```python
# 수정된 코드
movie = MovieRepository(db).get_with_details(db_review.movie_id)
genre = movie.genres[0].genre if movie and movie.genres else None  # ✓ 첫 번째 장르 사용
```

## 수정된 파일
- `Bolrea-Malrea-Backend/api/reviews.py`
  - `create_review()` 함수 (line ~90)
  - `update_review()` 함수 (line ~180)

## 테스트 결과

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

### 수정 후 (수동 업데이트 실행)
```json
{
  "review": {
    "review_count": 1,
    "genres": {
      "애니메이션": {
        "emotion_scores": {...},
        "narrative_traits": {...},
        "ending_preference": {...},
        "direction_mood": {...},
        "character_relationship": {...}
      }
    },
    "global": {...}
  }
}
```

## 기존 데이터 복구
기존에 작성된 리뷰의 선호도 데이터를 복구하려면:

```bash
python test_manual_review_update.py
```

이 스크립트는:
1. 사용자의 기존 리뷰를 분석
2. 영화 장르를 올바르게 가져옴
3. `review.genres`에 장르별 데이터 저장
4. `review_count` 증가
5. `global` 재계산

## 향후 동작
이제 새로운 리뷰가 작성되면:
1. 영화의 첫 번째 장르를 가져옴
2. A-1 API로 리뷰 내용 분석
3. `review.genres[장르]`에 분석 결과 저장
4. `review.global`에 누적 평균 저장
5. `review_count` 증가
6. `global` 재계산 (baseline 30% + review.global 70%)

## 검증 스크립트
- `test_review_genre_update.py`: 현재 상태 확인
- `test_manual_review_update.py`: 수동 업데이트 실행
- `check_db_detail.py`: 상세 데이터 확인

## 날짜
2024-02-27
