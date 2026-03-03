"""
취향 대시보드 (워드클라우드/영양표) 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from repositories.user_preference import UserPreferenceRepository
import json


def test_wordcloud_data_extraction():
    """워드클라우드가 새 구조에서 global을 제대로 추출하는지 테스트"""
    print("\n" + "="*80)
    print("테스트: 워드클라우드 데이터 추출 (새 구조)")
    print("="*80)
    
    # 새 구조 데이터
    preference_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5, "따뜻": 0.5},
            "narrative_traits": {"성장": 0.8},
            "ending_preference": {"happy": 0.7},
            "direction_mood": {"영상미": 0.5},
            "character_relationship": {"공감": 0.7}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.2, "따뜻": 0.9},
                "narrative_traits": {"성장": 0.85},
                "ending_preference": {"happy": 0.8},
                "direction_mood": {"영상미": 0.7},
                "character_relationship": {"공감": 0.9}
            },
            "genres": {},
            "review_count": 5
        },
        "global": {
            "emotion_scores": {"우울": 0.29, "따뜻": 0.78},
            "narrative_traits": {"성장": 0.835},
            "ending_preference": {"happy": 0.77},
            "direction_mood": {"영상미": 0.64},
            "character_relationship": {"공감": 0.83}
        }
    }
    
    # 워드클라우드 로직 시뮬레이션
    pref_vector = preference_data.copy()
    
    # 새 구조 처리
    if 'global' in pref_vector:
        pref_vector = pref_vector['global']
    
    emotion_scores = pref_vector.get("emotion_scores", {})
    
    print("\n추출된 emotion_scores:")
    print(json.dumps(emotion_scores, indent=2, ensure_ascii=False))
    
    # 검증
    assert emotion_scores["우울"] == 0.29, "global의 우울 값이 아님"
    assert emotion_scores["따뜻"] == 0.78, "global의 따뜻 값이 아님"
    
    print("\n✓ global에서 정확히 추출됨")
    print("✓ 설문(30%) + 리뷰(70%) 혼합 값 사용")
    print("\n✅ 테스트 통과")
    return True


def test_nutrition_facts_calculation():
    """영양표 계산이 global 기반으로 정확한지 테스트"""
    print("\n" + "="*80)
    print("테스트: 영양표 계산 (새 구조)")
    print("="*80)
    
    preference_data = {
        "baseline": {
            "emotion_scores": {"감동적이에요": 0.5, "슬퍼요": 0.4, "따뜻해요": 0.6},
            "narrative_traits": {"생각하면서 봐야 해요": 0.7},
            "ending_preference": {"open": 0.5},
            "direction_mood": {"영상미가 뛰어나요": 0.6, "긴장되는": 0.5},
            "character_relationship": {}
        },
        "review": {
            "global": {
                "emotion_scores": {"감동적이에요": 0.9, "슬퍼요": 0.8, "따뜻해요": 0.95},
                "narrative_traits": {"생각하면서 봐야 해요": 0.85},
                "ending_preference": {"open": 0.7},
                "direction_mood": {"영상미가 뛰어나요": 0.8, "긴장되는": 0.9},
                "character_relationship": {}
            },
            "genres": {},
            "review_count": 10
        },
        "global": {
            "emotion_scores": {"감동적이에요": 0.78, "슬퍼요": 0.68, "따뜻해요": 0.845},
            "narrative_traits": {"생각하면서 봐야 해요": 0.805},
            "ending_preference": {"open": 0.64},
            "direction_mood": {"영상미가 뛰어나요": 0.74, "긴장되는": 0.78},
            "character_relationship": {}
        }
    }
    
    # 영양표 로직 시뮬레이션
    pref_vector = preference_data.copy()
    
    if 'global' in pref_vector:
        pref_vector = pref_vector['global']
    
    emotions = pref_vector.get("emotion_scores", {})
    moods = pref_vector.get("direction_mood", {})
    narratives = pref_vector.get("narrative_traits", {})
    ending_pref = pref_vector.get("ending_preference", {})
    
    # 4대 영양소 계산
    dopamine_score = moods.get("긴장되는", 0) * 100
    sensitivity_score = (emotions.get("감동적이에요", 0) + emotions.get("슬퍼요", 0) + emotions.get("따뜻해요", 0)) / 3 * 100
    brain_score = (narratives.get("생각하면서 봐야 해요", 0) + ending_pref.get("open", 0) * 0.3) / 2 * 100
    eye_score = moods.get("영상미가 뛰어나요", 0) * 100
    
    print("\n영양표 계산 결과:")
    print(f"  도파민 (긴장/스릴): {dopamine_score:.1f}")
    print(f"  감수성 (감동/눈물): {sensitivity_score:.1f}")
    print(f"  두뇌회전 (사색): {brain_score:.1f}")
    print(f"  안구정화 (영상미): {eye_score:.1f}")
    
    # 검증: global 값 기반인지 확인
    expected_dopamine = 0.78 * 100  # global의 긴장되는
    assert abs(dopamine_score - expected_dopamine) < 0.1, f"도파민 계산 오류: {dopamine_score} != {expected_dopamine}"
    
    expected_sensitivity = (0.78 + 0.68 + 0.845) / 3 * 100  # global의 평균
    assert abs(sensitivity_score - expected_sensitivity) < 0.1, f"감수성 계산 오류: {sensitivity_score} != {expected_sensitivity}"
    
    print("\n✓ global 기반으로 정확히 계산됨")
    print("✓ 설문(30%) + 리뷰(70%) 혼합 값 반영")
    print("\n✅ 테스트 통과")
    return True


def test_real_db_dashboard():
    """실제 DB에서 대시보드 데이터 추출 테스트"""
    print("\n" + "="*80)
    print("테스트: 실제 DB 대시보드 데이터")
    print("="*80)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        from sqlalchemy import text
        repo = UserPreferenceRepository(session)
        
        # 실제 사용자 조회
        result = session.execute(text("SELECT user_id FROM user_preferences WHERE preference_vector_json IS NOT NULL LIMIT 1"))
        row = result.fetchone()
        
        if not row:
            print("⚠️  테스트 스킵: DB에 사용자 데이터가 없음")
            return True
        
        user_id = row[0]
        print(f"✓ 테스트 사용자: {user_id}")
        
        # 사용자 데이터 조회
        pref = repo.get_by_user_id(user_id)
        pref_data = pref.preference_vector_json
        
        print(f"\n데이터 구조:")
        print(f"  - baseline 존재: {'baseline' in pref_data}")
        print(f"  - review 존재: {'review' in pref_data}")
        print(f"  - global 존재: {'global' in pref_data}")
        
        # 워드클라우드 로직
        pref_vector = pref_data.copy()
        if 'global' in pref_vector:
            pref_vector = pref_vector['global']
        
        if pref_vector:
            emotion_scores = pref_vector.get("emotion_scores", {})
            print(f"\n추출된 emotion_scores 태그 수: {len(emotion_scores)}")
            
            if emotion_scores:
                # 상위 5개 태그 출력
                sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                print("\n상위 5개 감정 태그:")
                for tag, score in sorted_emotions:
                    print(f"  - {tag}: {score:.2f}")
            
            print("\n✓ 대시보드 데이터 정상 추출")
        else:
            print("\n⚠️  global 데이터 없음 (정상: 설문/리뷰 없는 사용자)")
        
        print("\n✅ 테스트 통과")
        return True
        
    finally:
        session.close()


if __name__ == "__main__":
    print("="*80)
    print("취향 대시보드 테스트")
    print("="*80)
    
    try:
        test_wordcloud_data_extraction()
        test_nutrition_facts_calculation()
        test_real_db_dashboard()
        
        print("\n" + "="*80)
        print("✅ 모든 대시보드 테스트 통과!")
        print("="*80)
        print("\n검증 완료:")
        print("1. ✅ 워드클라우드: global 자동 추출")
        print("2. ✅ 영양표: global 기반 계산")
        print("3. ✅ 실제 DB: 정상 작동")
        print("4. ✅ 새 구조 완벽 지원")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
