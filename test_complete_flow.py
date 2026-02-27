"""
Complete flow test: 신규 사용자 회원가입 → 설문 → 리뷰 작성 → 추천
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from repositories.user_preference import UserPreferenceRepository
from utils.preference_helper import (
    get_preference_for_recommendation,
    is_new_structure,
    get_structure_info
)
import json

# Test user ID
USER_ID = "user_7a351b0ba78840e5b35c72ae2d551724"

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("=" * 80)
    print("전체 플로우 테스트")
    print("=" * 80)
    
    pref_repo = UserPreferenceRepository(session)
    pref = pref_repo.get_by_user_id(USER_ID)
    
    if not pref:
        print(f"❌ 사용자를 찾을 수 없습니다: {USER_ID}")
        sys.exit(1)
    
    print(f"\n✓ 사용자: {USER_ID}")
    
    # 1. 구조 확인
    print(f"\n1. 데이터 구조 확인")
    print(f"   - 새 구조 사용: {is_new_structure(pref.preference_vector_json)}")
    
    structure_info = get_structure_info(pref.preference_vector_json)
    print(f"   - baseline 존재: {structure_info['has_baseline']}")
    print(f"   - review 존재: {structure_info['has_review']}")
    print(f"   - global 존재: {structure_info['has_global']}")
    
    # 2. baseline 확인
    print(f"\n2. Baseline (설문 기반)")
    baseline = pref.preference_vector_json.get('baseline', {})
    if baseline:
        print(f"   ✓ Baseline 데이터 있음")
        for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
            if category in baseline and baseline[category]:
                print(f"     - {category}: {len(baseline[category])} tags")
    else:
        print(f"   ⚠️  Baseline 데이터 없음 (설문 미완료)")
    
    # 3. review 확인
    print(f"\n3. Review (리뷰 기반)")
    review = pref.preference_vector_json.get('review', {})
    if review:
        print(f"   ✓ Review 데이터 있음")
        print(f"     - review_count: {review.get('review_count', 0)}")
        print(f"     - last_updated: {review.get('last_updated', 'N/A')}")
        
        genres = review.get('genres', {})
        if genres:
            print(f"     - 장르별 데이터:")
            for genre, data in genres.items():
                print(f"       * {genre}:")
                for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
                    if category in data and data[category]:
                        print(f"         - {category}: {len(data[category])} tags")
        else:
            print(f"     ⚠️  장르별 데이터 없음")
        
        review_global = review.get('global', {})
        if review_global and any(review_global.get(cat) for cat in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']):
            print(f"     - review.global:")
            for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
                if category in review_global and review_global[category]:
                    print(f"       - {category}: {len(review_global[category])} tags")
        else:
            print(f"     ⚠️  review.global 데이터 없음")
    else:
        print(f"   ⚠️  Review 데이터 없음")
    
    # 4. global 확인
    print(f"\n4. Global (최종 추천용)")
    global_data = pref.preference_vector_json.get('global')
    if global_data:
        print(f"   ✓ Global 데이터 있음 (baseline 30% + review 70%)")
        for category in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship']:
            if category in global_data and global_data[category]:
                print(f"     - {category}: {len(global_data[category])} tags")
                # 샘플 출력
                sample = list(global_data[category].items())[:3]
                print(f"       샘플: {sample}")
    else:
        print(f"   ⚠️  Global 데이터 없음")
    
    # 5. 추천 시나리오 테스트
    print(f"\n5. 추천 시나리오 테스트")
    
    # 5-1. 장르 명시 없음 (global 사용)
    print(f"\n   시나리오 1: 장르 명시 없음 (예: '따뜻한 영화 추천해줘')")
    pref_for_rec = get_preference_for_recommendation(pref.preference_vector_json, genre=None)
    if pref_for_rec:
        print(f"   ✓ 추천용 데이터 반환됨")
        print(f"     - 사용된 데이터: global")
        if 'emotion_scores' in pref_for_rec:
            sample = list(pref_for_rec['emotion_scores'].items())[:3]
            print(f"     - emotion_scores 샘플: {sample}")
    else:
        print(f"   ❌ 추천용 데이터 없음")
    
    # 5-2. 장르 명시 (애니메이션)
    print(f"\n   시나리오 2: 장르 명시 (예: '재미있는 애니메이션 추천해줘')")
    pref_for_rec = get_preference_for_recommendation(pref.preference_vector_json, genre='애니메이션')
    if pref_for_rec:
        print(f"   ✓ 추천용 데이터 반환됨")
        if '애니메이션' in review.get('genres', {}):
            print(f"     - 사용된 데이터: baseline + review.genres['애니메이션']")
        else:
            print(f"     - 사용된 데이터: global (애니메이션 리뷰 없음)")
        if 'emotion_scores' in pref_for_rec:
            sample = list(pref_for_rec['emotion_scores'].items())[:3]
            print(f"     - emotion_scores 샘플: {sample}")
    else:
        print(f"   ❌ 추천용 데이터 없음")
    
    # 5-3. 장르 명시 (드라마 - 리뷰 없음)
    print(f"\n   시나리오 3: 장르 명시 (예: '재미있는 드라마 추천해줘') - 리뷰 없음")
    pref_for_rec = get_preference_for_recommendation(pref.preference_vector_json, genre='드라마')
    if pref_for_rec:
        print(f"   ✓ 추천용 데이터 반환됨")
        if '드라마' in review.get('genres', {}):
            print(f"     - 사용된 데이터: baseline + review.genres['드라마']")
        else:
            print(f"     - 사용된 데이터: global (드라마 리뷰 없음)")
        if 'emotion_scores' in pref_for_rec:
            sample = list(pref_for_rec['emotion_scores'].items())[:3]
            print(f"     - emotion_scores 샘플: {sample}")
    else:
        print(f"   ❌ 추천용 데이터 없음")
    
    # 6. 요약
    print(f"\n" + "=" * 80)
    print(f"요약")
    print(f"=" * 80)
    
    has_baseline = baseline and any(baseline.get(cat) for cat in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship'])
    has_review = review and review.get('review_count', 0) > 0
    has_global = global_data and any(global_data.get(cat) for cat in ['emotion_scores', 'narrative_traits', 'ending_preference', 'direction_mood', 'character_relationship'])
    
    print(f"✓ 설문 완료: {'예' if has_baseline else '아니오'}")
    print(f"✓ 리뷰 작성: {'예 (' + str(review.get('review_count', 0)) + '개)' if has_review else '아니오'}")
    print(f"✓ 추천 가능: {'예' if has_global else '아니오'}")
    
    if has_baseline and has_review and has_global:
        print(f"\n✅ 모든 기능이 정상 작동합니다!")
    elif has_baseline and has_global:
        print(f"\n⚠️  설문은 완료했지만 리뷰가 없습니다. 추천은 가능합니다.")
    elif has_review and has_global:
        print(f"\n⚠️  리뷰는 있지만 설문을 하지 않았습니다. 추천은 가능합니다.")
    else:
        print(f"\n❌ 설문 또는 리뷰가 필요합니다.")
    
finally:
    session.close()
