"""
Test script to verify review API updates genre-specific data correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from repositories.user_preference import UserPreferenceRepository
from repositories.review import ReviewRepository
from repositories.movie import MovieRepository
import json

# Test user ID
USER_ID = "user_7a351b0ba78840e5b35c72ae2d551724"

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("=" * 80)
    print("리뷰 장르별 업데이트 테스트")
    print("=" * 80)
    
    # 1. 사용자 선호도 조회
    pref_repo = UserPreferenceRepository(session)
    pref = pref_repo.get_by_user_id(USER_ID)
    
    if not pref:
        print(f"❌ 사용자를 찾을 수 없습니다: {USER_ID}")
        sys.exit(1)
    
    print(f"\n✓ 사용자 찾음: {USER_ID}")
    
    # 2. 현재 상태 출력
    print(f"\n현재 선호도 상태:")
    print(f"  - review_count: {pref.preference_vector_json['review']['review_count']}")
    print(f"  - genres: {list(pref.preference_vector_json['review']['genres'].keys())}")
    
    if pref.preference_vector_json['review']['genres']:
        print(f"\n  장르별 데이터:")
        for genre, data in pref.preference_vector_json['review']['genres'].items():
            print(f"    - {genre}:")
            for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
                if category in data and data[category]:
                    sample_tags = list(data[category].items())[:3]
                    print(f"      {category}: {len(data[category])} tags, 샘플: {sample_tags}")
    
    # 3. 사용자의 리뷰 조회
    review_repo = ReviewRepository(session)
    reviews = review_repo.get_by_user(USER_ID, skip=0, limit=10)
    
    print(f"\n사용자 리뷰 목록 ({len(reviews)}개):")
    for review in reviews:
        movie = MovieRepository(session).get_with_details(review.movie_id)
        genres = [g.genre for g in movie.genres] if movie and movie.genres else []
        print(f"  - 리뷰 ID: {review.id}, 영화 ID: {review.movie_id}, 장르: {genres}, 평점: {review.rating}")
        if review.content:
            print(f"    내용: {review.content[:50]}...")
    
    # 4. 장르별 분석
    print(f"\n장르별 리뷰 분석:")
    genre_counts = {}
    for review in reviews:
        movie = MovieRepository(session).get_with_details(review.movie_id)
        if movie and movie.genres:
            genre = movie.genres[0].genre
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    for genre, count in genre_counts.items():
        print(f"  - {genre}: {count}개 리뷰")
    
    # 5. 문제 진단
    print(f"\n문제 진단:")
    if not pref.preference_vector_json['review']['genres']:
        print(f"  ⚠️  review.genres가 비어있습니다!")
        print(f"  원인: 리뷰 작성 시 장르 정보가 제대로 저장되지 않았을 수 있습니다.")
    else:
        stored_genres = set(pref.preference_vector_json['review']['genres'].keys())
        reviewed_genres = set(genre_counts.keys())
        
        if stored_genres != reviewed_genres:
            print(f"  ⚠️  저장된 장르와 리뷰한 장르가 일치하지 않습니다!")
            print(f"    저장된 장르: {stored_genres}")
            print(f"    리뷰한 장르: {reviewed_genres}")
            print(f"    누락된 장르: {reviewed_genres - stored_genres}")
        else:
            print(f"  ✓ 장르 데이터가 정상적으로 저장되어 있습니다.")
    
    # 6. global 상태 확인
    print(f"\nglobal 상태:")
    if pref.preference_vector_json.get('global'):
        print(f"  ✓ global이 계산되어 있습니다.")
        # 샘플 출력
        if 'emotion_scores' in pref.preference_vector_json['global']:
            sample = list(pref.preference_vector_json['global']['emotion_scores'].items())[:5]
            print(f"    emotion_scores 샘플: {sample}")
    else:
        print(f"  ⚠️  global이 None입니다.")
    
    print(f"\n" + "=" * 80)
    print(f"테스트 완료")
    print(f"=" * 80)
    
finally:
    session.close()
