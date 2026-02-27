"""
Phase 4 테스트: 리뷰 API가 review 데이터를 업데이트하는지 확인
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


def test_update_review_new_user():
    """신규 사용자: 첫 리뷰로 review 생성"""
    print("\n" + "="*80)
    print("테스트 1: 신규 사용자 - 첫 리뷰로 review 생성")
    print("="*80)
    
    # 신규 사용자 (데이터 없음)
    existing_data = None
    
    # 리뷰 분석 결과
    analyzed_preference = {
        "emotion_scores": {"우울": 0.2, "따뜻": 0.8},
        "narrative_traits": {"성장": 0.9},
        "ending_preference": {"happy": 0.8},
        "direction_mood": {"영상미": 0.7},
        "character_relationship": {"공감": 0.9}
    }
    
    # review 업데이트
    result = update_review_from_analysis(existing_data, analyzed_preference, genre="드라마")
    
    print("\n결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증
    assert "baseline" in result, "baseline 키가 없음"
    assert "review" in result, "review 키가 없음"
    assert "global" in result, "global 키가 없음"
    assert result["review"]["review_count"] == 1, "review_count가 1이 아님"
    assert result["review"]["global"]["emotion_scores"]["우울"] == 0.2, "review.global이 업데이트되지 않음"
    assert "드라마" in result["review"]["genres"], "장르가 저장되지 않음"
    assert result["global"] is not None, "global이 계산되지 않음"
    assert result["global"]["emotion_scores"]["우울"] == 0.2, "global이 review와 같아야 함 (baseline 없음)"
    
    print("\n✅ 테스트 1 통과")
    return True


def test_update_review_existing_user():
    """기존 사용자: review 누적, baseline 보존"""
    print("\n" + "="*80)
    print("테스트 2: 기존 사용자 - review 누적, baseline 보존")
    print("="*80)
    
    # 기존 데이터 (baseline 있음, review 1개)
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
                "emotion_scores": {"우울": 0.3, "따뜻": 0.7},
                "narrative_traits": {"성장": 0.8},
                "ending_preference": {"happy": 0.8},
                "direction_mood": {"영상미": 0.6},
                "character_relationship": {"공감": 0.8}
            },
            "genres": {
                "SF": {
                    "emotion_scores": {"긴장": 0.9},
                    "narrative_traits": {},
                    "ending_preference": {},
                    "direction_mood": {},
                    "character_relationship": {}
                }
            },
            "review_count": 1,
            "last_updated": "2024-02-27T10:00:00Z"
        },
        "global": None
    }
    
    # 새로운 리뷰 분석 결과
    new_review_analysis = {
        "emotion_scores": {"우울": 0.1, "따뜻": 0.9, "긴장": 0.5},
        "narrative_traits": {"성장": 0.9, "관계": 0.8},
        "ending_preference": {"happy": 0.9},
        "direction_mood": {"영상미": 0.8},
        "character_relationship": {"공감": 0.9}
    }
    
    # review 업데이트
    result = update_review_from_analysis(existing_data, new_review_analysis, genre="로맨스")
    
    print("\n결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증
    assert result["baseline"]["emotion_scores"]["우울"] == 0.5, "baseline이 변경됨 (보존되어야 함)"
    assert result["review"]["review_count"] == 2, "review_count가 2가 아님"
    
    # 누적 평균 확인 (0.3 * 1 + 0.1 * 1) / 2 = 0.2
    expected_avg = (0.3 + 0.1) / 2
    assert abs(result["review"]["global"]["emotion_scores"]["우울"] - expected_avg) < 0.01, f"누적 평균이 잘못됨: {result['review']['global']['emotion_scores']['우울']} != {expected_avg}"
    
    assert "로맨스" in result["review"]["genres"], "새 장르가 저장되지 않음"
    assert "SF" in result["review"]["genres"], "기존 장르가 보존되지 않음"
    assert result["review"]["last_updated"] is not None, "last_updated가 업데이트되지 않음"
    
    # global 가중평균 확인: baseline(0.5) * 0.3 + review(0.2) * 0.7 = 0.15 + 0.14 = 0.29
    expected_global = 0.5 * 0.3 + expected_avg * 0.7
    assert result["global"] is not None, "global이 계산되지 않음"
    assert abs(result["global"]["emotion_scores"]["우울"] - expected_global) < 0.01, f"global 가중평균이 잘못됨: {result['global']['emotion_scores']['우울']} != {expected_global}"
    
    print("\n✅ 테스트 2 통과")
    return True


def test_update_review_multiple_times():
    """여러 번 리뷰: 누적 평균 계산 확인"""
    print("\n" + "="*80)
    print("테스트 3: 여러 번 리뷰 - 누적 평균 계산")
    print("="*80)
    
    # 초기 데이터
    data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        },
        "review": {
            "global": {
                "emotion_scores": {},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            },
            "genres": {},
            "review_count": 0,
            "last_updated": None
        },
        "global": None
    }
    
    # 첫 번째 리뷰: 우울 0.8
    print("\n[1번째 리뷰] 우울: 0.8")
    data = update_review_from_analysis(
        data,
        {"emotion_scores": {"우울": 0.8}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}},
        genre="드라마"
    )
    print(f"  review_count: {data['review']['review_count']}")
    print(f"  review.global.emotion_scores.우울: {data['review']['global']['emotion_scores']['우울']}")
    assert data['review']['review_count'] == 1
    assert data['review']['global']['emotion_scores']['우울'] == 0.8
    
    # 두 번째 리뷰: 우울 0.4
    print("\n[2번째 리뷰] 우울: 0.4")
    data = update_review_from_analysis(
        data,
        {"emotion_scores": {"우울": 0.4}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}},
        genre="코미디"
    )
    print(f"  review_count: {data['review']['review_count']}")
    print(f"  review.global.emotion_scores.우울: {data['review']['global']['emotion_scores']['우울']}")
    expected = (0.8 + 0.4) / 2  # 0.6
    assert data['review']['review_count'] == 2
    assert abs(data['review']['global']['emotion_scores']['우울'] - expected) < 0.01
    
    # 세 번째 리뷰: 우울 0.2
    print("\n[3번째 리뷰] 우울: 0.2")
    data = update_review_from_analysis(
        data,
        {"emotion_scores": {"우울": 0.2}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}},
        genre="액션"
    )
    print(f"  review_count: {data['review']['review_count']}")
    print(f"  review.global.emotion_scores.우울: {data['review']['global']['emotion_scores']['우울']}")
    expected = (0.8 + 0.4 + 0.2) / 3  # 0.4666...
    assert data['review']['review_count'] == 3
    assert abs(data['review']['global']['emotion_scores']['우울'] - expected) < 0.01
    
    # baseline은 변경되지 않음
    assert data['baseline']['emotion_scores']['우울'] == 0.5, "baseline이 변경됨"
    
    print("\n✅ 테스트 3 통과")
    return True


def test_real_db_update():
    """실제 DB 테스트: 리뷰 업데이트 후 확인"""
    print("\n" + "="*80)
    print("테스트 4: 실제 DB - 리뷰 업데이트 후 확인")
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
        
        original_review_count = original_data.get("review", {}).get("review_count", 0)
        print(f"✓ 기존 review_count: {original_review_count}")
        
        # 2. 리뷰 분석 결과로 review 업데이트
        print("\n[테스트] 리뷰 분석 결과로 review 업데이트")
        review_analysis = {
            "emotion_scores": {"테스트_리뷰_우울": 0.11, "테스트_리뷰_따뜻": 0.99},
            "narrative_traits": {"테스트_리뷰_성장": 0.88},
            "ending_preference": {"happy": 0.77},
            "direction_mood": {"테스트_리뷰_영상미": 0.66},
            "character_relationship": {"테스트_리뷰_공감": 0.55}
        }
        
        updated_data = update_review_from_analysis(original_data, review_analysis, genre="테스트장르")
        repo.upsert(
            user_id=test_user_id,
            preference_vector_json=updated_data,
            boost_tags=original_boost_tags
        )
        
        # 3. 확인
        pref = repo.get_by_user_id(test_user_id)
        print(f"✓ review 업데이트 확인:")
        print(f"  - review_count: {pref.preference_vector_json['review']['review_count']} (이전: {original_review_count})")
        print(f"  - 테스트_리뷰_우울: {pref.preference_vector_json['review']['global']['emotion_scores'].get('테스트_리뷰_우울')}")
        print(f"  - 테스트장르 존재: {'테스트장르' in pref.preference_vector_json['review']['genres']}")
        
        # 검증
        assert pref.preference_vector_json["review"]["review_count"] == original_review_count + 1, "review_count가 증가하지 않음"
        assert "테스트_리뷰_우울" in pref.preference_vector_json["review"]["global"]["emotion_scores"], "review.global이 업데이트되지 않음"
        assert "테스트장르" in pref.preference_vector_json["review"]["genres"], "장르가 저장되지 않음"
        
        # baseline이 보존되었는지 확인
        if "baseline" in original_data and original_data["baseline"]:
            print(f"✓ baseline 보존 확인")
            # baseline의 첫 번째 키 확인
            for category in ["emotion_scores", "narrative_traits", "ending_preference", "direction_mood", "character_relationship"]:
                if category in original_data["baseline"] and original_data["baseline"][category]:
                    first_key = list(original_data["baseline"][category].keys())[0]
                    assert pref.preference_vector_json["baseline"][category][first_key] == original_data["baseline"][category][first_key], f"baseline.{category}가 변경됨"
                    print(f"  - baseline.{category} 보존됨")
                    break
        
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
    print("Phase 4 테스트: 리뷰 API review 업데이트")
    print("="*80)
    
    try:
        test_update_review_new_user()
        test_update_review_existing_user()
        test_update_review_multiple_times()
        test_real_db_update()
        
        print("\n" + "="*80)
        print("✅ 모든 테스트 통과!")
        print("="*80)
        print("\n다음 단계:")
        print("1. 실제 리뷰 작성 시 정상 작동 확인")
        print("2. Phase 5로 진행: global 계산 로직 구현")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
