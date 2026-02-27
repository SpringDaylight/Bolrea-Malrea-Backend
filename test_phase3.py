"""
Phase 3 테스트: 설문 API가 baseline만 업데이트하는지 확인
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from repositories.user_preference import UserPreferenceRepository
from utils.preference_helper import update_baseline
import json


def test_update_baseline_new_user():
    """신규 사용자: baseline 생성"""
    print("\n" + "="*80)
    print("테스트 1: 신규 사용자 - baseline 생성")
    print("="*80)
    
    # 신규 사용자 (데이터 없음)
    existing_data = None
    
    # 설문 결과
    survey_result = {
        "emotion_scores": {"우울": 0.8, "따뜻": 0.5},
        "narrative_traits": {"성장": 0.9},
        "ending_preference": {"happy": 0.7},
        "direction_mood": {"영상미": 0.6},
        "character_relationship": {"공감": 0.8}
    }
    
    # baseline 업데이트
    result = update_baseline(existing_data, survey_result)
    
    print("\n결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증
    assert "baseline" in result, "baseline 키가 없음"
    assert "review" in result, "review 키가 없음"
    assert "global" in result, "global 키가 없음"
    assert result["baseline"] == survey_result, "baseline이 설문 결과와 다름"
    assert result["review"]["review_count"] == 0, "review_count가 0이 아님"
    assert result["global"] is not None, "global이 계산되지 않음"
    assert result["global"]["emotion_scores"]["우울"] == 0.8, "global이 baseline과 같아야 함 (review 없음)"
    
    print("\n✅ 테스트 1 통과")
    return True


def test_update_baseline_existing_user():
    """기존 사용자: baseline만 업데이트, review 보존"""
    print("\n" + "="*80)
    print("테스트 2: 기존 사용자 - baseline 업데이트, review 보존")
    print("="*80)
    
    # 기존 데이터 (리뷰 데이터 있음)
    existing_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5, "따뜻": 0.5},
            "narrative_traits": {"성장": 0.8},
            "ending_preference": {"happy": 0.7},
            "direction_mood": {"영상미": 0.5},
            "character_relationship": {"공감": 0.7}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.2, "따뜻": 0.8},
                "narrative_traits": {"성장": 0.9},
                "ending_preference": {"happy": 0.8},
                "direction_mood": {"영상미": 0.7},
                "character_relationship": {"공감": 0.9}
            },
            "genres": {
                "SF": {"emotion_scores": {"긴장": 0.9}},
                "Romance": {"emotion_scores": {"따뜻": 1.0}}
            },
            "review_count": 15,
            "last_updated": "2024-02-27T10:30:00Z"
        },
        "global": {
            "emotion_scores": {"우울": 0.35, "따뜻": 0.65},
            "narrative_traits": {"성장": 0.85},
            "ending_preference": {"happy": 0.75},
            "direction_mood": {"영상미": 0.6},
            "character_relationship": {"공감": 0.8}
        }
    }
    
    # 새로운 설문 결과 (다시 설문함)
    new_survey_result = {
        "emotion_scores": {"우울": 0.1, "따뜻": 0.9, "긴장": 0.7},
        "narrative_traits": {"성장": 0.5, "관계": 0.8},
        "ending_preference": {"happy": 0.9, "open": 0.3},
        "direction_mood": {"영상미": 0.8, "연출": 0.6},
        "character_relationship": {"공감": 0.9, "성장": 0.7}
    }
    
    # baseline 업데이트
    result = update_baseline(existing_data, new_survey_result)
    
    print("\n결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증
    assert result["baseline"] == new_survey_result, "baseline이 새 설문 결과로 업데이트되지 않음"
    assert result["review"]["review_count"] == 15, "review_count가 보존되지 않음"
    assert result["review"]["genres"]["SF"]["emotion_scores"]["긴장"] == 0.9, "review.genres가 보존되지 않음"
    assert result["review"]["global"]["emotion_scores"]["우울"] == 0.2, "review.global이 보존되지 않음"
    assert result["global"] is not None, "global이 계산되지 않음"
    # global은 baseline(0.1) * 0.3 + review(0.2) * 0.7 = 0.03 + 0.14 = 0.17
    expected_global_uul = 0.1 * 0.3 + 0.2 * 0.7
    assert abs(result["global"]["emotion_scores"]["우울"] - expected_global_uul) < 0.01, f"global 가중평균이 잘못됨: {result['global']['emotion_scores']['우울']} != {expected_global_uul}"
    
    print("\n✅ 테스트 2 통과")
    return True


def test_update_baseline_old_structure():
    """기존 구조 사용자: 마이그레이션 + baseline 업데이트"""
    print("\n" + "="*80)
    print("테스트 3: 기존 구조 사용자 - 마이그레이션 + baseline 업데이트")
    print("="*80)
    
    # 기존 구조 데이터
    old_structure_data = {
        "emotion_scores": {"우울": 0.5, "따뜻": 0.5},
        "narrative_traits": {"성장": 0.8},
        "ending_preference": {"happy": 0.7},
        "direction_mood": {"영상미": 0.5},
        "character_relationship": {"공감": 0.7}
    }
    
    # 새로운 설문 결과
    new_survey_result = {
        "emotion_scores": {"우울": 0.2, "따뜻": 0.8},
        "narrative_traits": {"성장": 0.9, "관계": 0.7},
        "ending_preference": {"happy": 0.8},
        "direction_mood": {"영상미": 0.7},
        "character_relationship": {"공감": 0.9}
    }
    
    # baseline 업데이트 (자동 마이그레이션)
    result = update_baseline(old_structure_data, new_survey_result)
    
    print("\n결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증
    assert "baseline" in result, "baseline 키가 없음"
    assert "review" in result, "review 키가 없음"
    assert "global" in result, "global 키가 없음"
    assert result["baseline"] == new_survey_result, "baseline이 새 설문 결과로 업데이트되지 않음"
    assert result["review"]["review_count"] == 0, "review_count가 0이 아님"
    assert result["global"] is not None, "global이 계산되지 않음"
    assert result["global"]["emotion_scores"]["우울"] == 0.2, "global이 baseline과 같아야 함 (review 없음)"
    
    print("\n✅ 테스트 3 통과")
    return True


def test_real_db_update():
    """실제 DB 테스트: 설문 저장 후 확인"""
    print("\n" + "="*80)
    print("테스트 4: 실제 DB - 설문 저장 후 확인")
    print("="*80)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        from sqlalchemy import text
        repo = UserPreferenceRepository(session)
        
        # 실제 존재하는 사용자 ID 가져오기
        result = session.execute(text("SELECT user_id FROM user_preferences LIMIT 1"))
        row = result.fetchone()
        
        if not row:
            print("⚠️  테스트 스킵: DB에 사용자 데이터가 없음")
            return True
        
        test_user_id = row[0]
        print(f"✓ 테스트 사용자: {test_user_id}")
        
        # 1. 기존 데이터 백업
        original_pref = repo.get_by_user_id(test_user_id)
        original_data = original_pref.preference_vector_json.copy()
        original_boost_tags = original_pref.boost_tags.copy() if original_pref.boost_tags else []
        
        print(f"✓ 기존 데이터 백업 완료")
        print(f"  - baseline 키 존재: {'baseline' in original_data}")
        print(f"  - review 키 존재: {'review' in original_data}")
        
        # 2. 새로운 설문 결과로 baseline 업데이트
        print("\n[테스트] 새로운 설문으로 baseline 업데이트")
        new_survey = {
            "emotion_scores": {"테스트_우울": 0.99, "테스트_따뜻": 0.88},
            "narrative_traits": {"테스트_성장": 0.77},
            "ending_preference": {"happy": 0.66},
            "direction_mood": {"테스트_영상미": 0.55},
            "character_relationship": {"테스트_공감": 0.44}
        }
        
        updated_data = update_baseline(original_data, new_survey)
        repo.upsert(
            user_id=test_user_id,
            preference_vector_json=updated_data,
            boost_tags=["테스트태그1", "테스트태그2"]
        )
        
        # 3. 확인
        pref = repo.get_by_user_id(test_user_id)
        print(f"✓ baseline 업데이트 확인:")
        print(f"  - 테스트_우울: {pref.preference_vector_json['baseline']['emotion_scores'].get('테스트_우울')}")
        print(f"  - 테스트_성장: {pref.preference_vector_json['baseline']['narrative_traits'].get('테스트_성장')}")
        
        # review 데이터가 있었다면 보존되었는지 확인
        if 'review' in original_data and original_data['review'].get('review_count', 0) > 0:
            print(f"✓ review 데이터 보존 확인:")
            print(f"  - review_count: {pref.preference_vector_json['review']['review_count']}")
            assert pref.preference_vector_json['review']['review_count'] == original_data['review']['review_count'], "review_count가 보존되지 않음"
        
        # 검증
        assert pref.preference_vector_json["baseline"]["emotion_scores"]["테스트_우울"] == 0.99, "baseline이 업데이트되지 않음"
        assert pref.preference_vector_json["baseline"]["narrative_traits"]["테스트_성장"] == 0.77, "baseline이 업데이트되지 않음"
        
        print("\n✅ 테스트 4 통과")
        
        # 4. 원래 데이터로 복구
        print("\n[복구] 원래 데이터로 복구 중...")
        repo.upsert(
            user_id=test_user_id,
            preference_vector_json=original_data,
            boost_tags=original_boost_tags
        )
        print(f"✓ 원래 데이터로 복구 완료")
        
        return True
        
    finally:
        session.close()


if __name__ == "__main__":
    print("="*80)
    print("Phase 3 테스트: 설문 API baseline 업데이트")
    print("="*80)
    
    try:
        test_update_baseline_new_user()
        test_update_baseline_existing_user()
        test_update_baseline_old_structure()
        test_real_db_update()
        
        print("\n" + "="*80)
        print("✅ 모든 테스트 통과!")
        print("="*80)
        print("\n다음 단계:")
        print("1. 프론트엔드에서 설문 API 호출 시 정상 작동 확인")
        print("2. Phase 4로 진행: 리뷰 API가 review 업데이트하도록 수정")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
