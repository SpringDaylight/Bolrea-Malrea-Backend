"""
Manually trigger preference update for existing review to test the fix
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
from domain.a1_preference import analyze_preference
from utils.preference_helper import update_review_from_analysis
import json

# Test user ID and review ID
USER_ID = "user_7a351b0ba78840e5b35c72ae2d551724"
REVIEW_ID = 61

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("=" * 80)
    print("수동 리뷰 선호도 업데이트 테스트")
    print("=" * 80)
    
    # 1. 리뷰 조회
    review_repo = ReviewRepository(session)
    review = review_repo.get(REVIEW_ID)
    
    if not review:
        print(f"❌ 리뷰를 찾을 수 없습니다: {REVIEW_ID}")
        sys.exit(1)
    
    print(f"\n✓ 리뷰 찾음: ID={review.id}, 영화 ID={review.movie_id}")
    print(f"  내용: {review.content[:100] if review.content else 'No content'}...")
    
    # 2. 영화 장르 조회
    movie = MovieRepository(session).get_with_details(review.movie_id)
    if not movie:
        print(f"❌ 영화를 찾을 수 없습니다: {review.movie_id}")
        sys.exit(1)
    
    genres = [g.genre for g in movie.genres] if movie.genres else []
    print(f"\n✓ 영화 찾음: {movie.title}")
    print(f"  장르: {genres}")
    
    genre = genres[0] if genres else None
    print(f"  사용할 장르: {genre}")
    
    # 3. 사용자의 모든 리뷰 가져오기
    user_reviews = review_repo.get_by_user(USER_ID, skip=0, limit=100)
    print(f"\n✓ 사용자 리뷰 {len(user_reviews)}개 찾음")
    
    # 4. 리뷰 내용 분석
    review_texts = []
    for r in user_reviews:
        if r.content:
            review_texts.append(r.content)
    
    if not review_texts:
        print(f"❌ 분석할 리뷰 내용이 없습니다")
        sys.exit(1)
    
    combined_text = " ".join(review_texts[-10:])
    print(f"\n분석할 텍스트 (최근 10개 리뷰):")
    print(f"  {combined_text[:200]}...")
    
    # 5. A-1 API로 선호도 분석
    print(f"\nA-1 API로 선호도 분석 중...")
    try:
        user_profile = analyze_preference({
            "text": combined_text,
            "dislikes": ""
        })
        
        print(f"✓ 분석 완료")
        print(f"  emotion_scores: {len(user_profile['emotion_scores'])} tags")
        print(f"  narrative_traits: {len(user_profile['narrative_traits'])} tags")
        print(f"  direction_mood: {len(user_profile['direction_mood'])} tags")
        print(f"  character_relationship: {len(user_profile['character_relationship'])} tags")
        print(f"  ending_preference: {len(user_profile['ending_preference'])} tags")
        
        # 샘플 출력
        print(f"\n  emotion_scores 샘플:")
        for tag, score in list(user_profile['emotion_scores'].items())[:5]:
            print(f"    - {tag}: {score}")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 6. 분석 결과를 5개 카테고리로 구성
    analyzed_preference = {
        "emotion_scores": user_profile["emotion_scores"],
        "narrative_traits": user_profile["narrative_traits"],
        "direction_mood": user_profile["direction_mood"],
        "character_relationship": user_profile["character_relationship"],
        "ending_preference": user_profile["ending_preference"]
    }
    
    # 7. 기존 선호도 조회
    pref_repo = UserPreferenceRepository(session)
    existing_pref = pref_repo.get_by_user_id(USER_ID)
    
    if not existing_pref:
        print(f"❌ 사용자 선호도를 찾을 수 없습니다: {USER_ID}")
        sys.exit(1)
    
    print(f"\n✓ 기존 선호도 찾음")
    print(f"  현재 review_count: {existing_pref.preference_vector_json['review']['review_count']}")
    print(f"  현재 genres: {list(existing_pref.preference_vector_json['review']['genres'].keys())}")
    
    # 8. review 데이터 업데이트
    print(f"\nreview 데이터 업데이트 중 (장르: {genre})...")
    try:
        updated_preference_json = update_review_from_analysis(
            existing_pref.preference_vector_json,
            analyzed_preference,
            genre=genre
        )
        
        print(f"✓ 업데이트 완료")
        print(f"  새 review_count: {updated_preference_json['review']['review_count']}")
        print(f"  새 genres: {list(updated_preference_json['review']['genres'].keys())}")
        
        if genre in updated_preference_json['review']['genres']:
            genre_data = updated_preference_json['review']['genres'][genre]
            print(f"\n  {genre} 장르 데이터:")
            for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
                if category in genre_data and genre_data[category]:
                    print(f"    - {category}: {len(genre_data[category])} tags")
                    sample = list(genre_data[category].items())[:3]
                    print(f"      샘플: {sample}")
        
        # 9. DB에 저장
        print(f"\nDB에 저장 중...")
        pref_repo.upsert(
            user_id=USER_ID,
            preference_vector_json=updated_preference_json,
            boost_tags=user_profile.get("boost_tags", []),
            dislike_tags=user_profile.get("dislike_tags", []),
            penalty_tags=[]
        )
        
        print(f"✓ 저장 완료")
        
        # 10. 검증
        print(f"\n검증 중...")
        updated_pref = pref_repo.get_by_user_id(USER_ID)
        print(f"  review_count: {updated_pref.preference_vector_json['review']['review_count']}")
        print(f"  genres: {list(updated_pref.preference_vector_json['review']['genres'].keys())}")
        print(f"  global 존재: {updated_pref.preference_vector_json.get('global') is not None}")
        
        print(f"\n✅ 테스트 성공!")
        
    except Exception as e:
        print(f"❌ 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
finally:
    session.close()
