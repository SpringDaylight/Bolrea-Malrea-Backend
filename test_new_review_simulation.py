"""
Simulate creating a new review to test the complete flow
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

# Test user ID
USER_ID = "user_7a351b0ba78840e5b35c72ae2d551724"

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("=" * 80)
    print("신규 리뷰 작성 시뮬레이션")
    print("=" * 80)
    
    # 시뮬레이션: 사용자가 드라마 영화에 리뷰 작성
    print(f"\n시나리오: 사용자가 드라마 영화 '기생충'에 리뷰 작성")
    
    # 1. 현재 상태 확인
    pref_repo = UserPreferenceRepository(session)
    pref = pref_repo.get_by_user_id(USER_ID)
    
    print(f"\n1. 현재 상태")
    print(f"   - review_count: {pref.preference_vector_json['review']['review_count']}")
    print(f"   - genres: {list(pref.preference_vector_json['review']['genres'].keys())}")
    
    # 2. 리뷰 내용 (시뮬레이션)
    new_review_content = """
    정말 충격적이고 생각할 거리가 많은 영화였습니다. 
    계층 간의 갈등을 너무나 현실적으로 그려냈고, 
    반전이 정말 대단했어요. 
    배우들의 연기도 훌륭했고, 
    특히 송강호 배우의 연기가 인상적이었습니다.
    """
    
    print(f"\n2. 새 리뷰 내용")
    print(f"   {new_review_content.strip()[:100]}...")
    
    # 3. 사용자의 모든 리뷰 가져오기 (기존 + 새 리뷰)
    review_repo = ReviewRepository(session)
    existing_reviews = review_repo.get_by_user(USER_ID, skip=0, limit=100)
    
    all_review_texts = [r.content for r in existing_reviews if r.content]
    all_review_texts.append(new_review_content)
    
    combined_text = " ".join(all_review_texts[-10:])
    
    print(f"\n3. 분석할 텍스트 (기존 리뷰 + 새 리뷰)")
    print(f"   - 총 리뷰 수: {len(all_review_texts)}")
    print(f"   - 분석 대상: 최근 {min(10, len(all_review_texts))}개")
    
    # 4. A-1 API로 선호도 분석
    print(f"\n4. A-1 API로 선호도 분석")
    user_profile = analyze_preference({
        "text": combined_text,
        "dislikes": ""
    })
    
    analyzed_preference = {
        "emotion_scores": user_profile["emotion_scores"],
        "narrative_traits": user_profile["narrative_traits"],
        "direction_mood": user_profile["direction_mood"],
        "character_relationship": user_profile["character_relationship"],
        "ending_preference": user_profile["ending_preference"]
    }
    
    print(f"   ✓ 분석 완료")
    print(f"   - emotion_scores 샘플:")
    for tag, score in list(analyzed_preference['emotion_scores'].items())[:5]:
        print(f"     * {tag}: {score:.3f}")
    
    # 5. 영화 장르 (시뮬레이션: 드라마)
    genre = "드라마"
    print(f"\n5. 영화 장르: {genre}")
    
    # 6. review 데이터 업데이트
    print(f"\n6. review 데이터 업데이트")
    updated_preference_json = update_review_from_analysis(
        pref.preference_vector_json,
        analyzed_preference,
        genre=genre
    )
    
    print(f"   ✓ 업데이트 완료")
    print(f"   - 새 review_count: {updated_preference_json['review']['review_count']}")
    print(f"   - 새 genres: {list(updated_preference_json['review']['genres'].keys())}")
    
    # 7. 장르별 데이터 확인
    if genre in updated_preference_json['review']['genres']:
        print(f"\n7. {genre} 장르 데이터")
        genre_data = updated_preference_json['review']['genres'][genre]
        for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
            if category in genre_data and genre_data[category]:
                print(f"   - {category}: {len(genre_data[category])} tags")
                sample = list(genre_data[category].items())[:3]
                print(f"     샘플: {sample}")
    
    # 8. global 재계산 확인
    print(f"\n8. Global 재계산")
    if updated_preference_json.get('global'):
        print(f"   ✓ Global이 재계산되었습니다")
        print(f"   - emotion_scores 샘플:")
        for tag, score in list(updated_preference_json['global']['emotion_scores'].items())[:5]:
            print(f"     * {tag}: {score:.3f}")
    else:
        print(f"   ❌ Global 계산 실패")
    
    # 9. 추천 시나리오 테스트
    print(f"\n9. 추천 시나리오 테스트")
    from utils.preference_helper import get_preference_for_recommendation
    
    # 드라마 추천
    pref_for_drama = get_preference_for_recommendation(updated_preference_json, genre='드라마')
    if pref_for_drama:
        print(f"   ✓ '재미있는 드라마 추천해줘' → baseline + review.genres['드라마'] 사용")
        print(f"     emotion_scores 샘플: {list(pref_for_drama['emotion_scores'].items())[:3]}")
    
    # 애니메이션 추천
    pref_for_animation = get_preference_for_recommendation(updated_preference_json, genre='애니메이션')
    if pref_for_animation:
        print(f"   ✓ '재미있는 애니메이션 추천해줘' → baseline + review.genres['애니메이션'] 사용")
        print(f"     emotion_scores 샘플: {list(pref_for_animation['emotion_scores'].items())[:3]}")
    
    # 장르 명시 없음
    pref_for_general = get_preference_for_recommendation(updated_preference_json, genre=None)
    if pref_for_general:
        print(f"   ✓ '따뜻한 영화 추천해줘' → global 사용")
        print(f"     emotion_scores 샘플: {list(pref_for_general['emotion_scores'].items())[:3]}")
    
    print(f"\n" + "=" * 80)
    print(f"시뮬레이션 완료")
    print(f"=" * 80)
    print(f"\n✅ 새 리뷰 작성 시 다음과 같이 동작합니다:")
    print(f"   1. 리뷰 내용을 A-1 API로 분석")
    print(f"   2. 영화 장르를 가져옴 (첫 번째 장르)")
    print(f"   3. review.genres[장르]에 분석 결과 저장")
    print(f"   4. review.global에 누적 평균 저장")
    print(f"   5. review_count 증가")
    print(f"   6. global 재계산 (baseline 30% + review.global 70%)")
    print(f"   7. 장르별 추천 시 해당 장르 데이터 사용")
    
    print(f"\n⚠️  주의: 이 시뮬레이션은 DB에 저장하지 않습니다.")
    print(f"   실제 리뷰 작성은 프론트엔드에서 POST /api/reviews로 수행하세요.")
    
finally:
    session.close()
