"""
리뷰 데이터 수동 업데이트 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from repositories.user_preference import UserPreferenceRepository
from utils.preference_helper import update_review_from_analysis
import json

# 사용자 ID
USER_ID = "user_7a351b0ba78840e5b35c72ae2d551724"

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    repo = UserPreferenceRepository(session)
    
    # 현재 데이터 조회
    pref = repo.get_by_user_id(USER_ID)
    
    if not pref:
        print(f"❌ 사용자를 찾을 수 없습니다: {USER_ID}")
        sys.exit(1)
    
    print(f"✓ 사용자 찾음: {USER_ID}")
    print(f"\n현재 상태:")
    print(f"  - review_count: {pref.preference_vector_json['review']['review_count']}")
    print(f"  - genres: {list(pref.preference_vector_json['review']['genres'].keys())}")
    
    # 애니메이션 리뷰 데이터 추가 (예시)
    print(f"\n애니메이션 리뷰 데이터 추가 중...")
    
    test_review = {
        'emotion_scores': {
            '웃겨요': 0.85,
            '따뜻해요': 0.8,
            '감동적이에요': 0.9,
            '희망적이에요': 0.85,
            '밝은 분위기예요': 0.9
        },
        'narrative_traits': {
            '성장': 0.9,
            '전개가 빨라요': 0.8,
            '초반부터 몰입돼요': 0.85
        },
        'ending_preference': {
            'happy': 0.9,
            'bittersweet': 0.3
        },
        'direction_mood': {
            '영상미가 좋아요': 0.95,
            '색감이 예뻐요': 0.9,
            '배경이 매력적이에요': 0.85
        },
        'character_relationship': {
            '공감': 0.9,
            '캐릭터 성장이 잘 보여요': 0.85,
            '주인공이 매력적이에요': 0.8
        }
    }
    
    # 업데이트
    updated = update_review_from_analysis(
        pref.preference_vector_json,
        test_review,
        genre='애니메이션'
    )
    
    print(f"\n업데이트 후:")
    print(f"  - review_count: {updated['review']['review_count']}")
    print(f"  - genres: {list(updated['review']['genres'].keys())}")
    print(f"  - global 계산됨: {updated['global'] is not None}")
    
    if updated['global']:
        print(f"\n  global.emotion_scores 샘플:")
        for tag, score in list(updated['global']['emotion_scores'].items())[:5]:
            print(f"    - {tag}: {score:.2f}")
    
    # 저장
    print(f"\nDB에 저장 중...")
    repo.upsert(
        user_id=USER_ID,
        preference_vector_json=updated,
        boost_tags=pref.boost_tags,
        dislike_tags=pref.dislike_tags,
        penalty_tags=pref.penalty_tags
    )
    
    print(f"\n✅ 완료!")
    print(f"\n확인:")
    print(f"  python check_db_detail.py {USER_ID}")
    
finally:
    session.close()
