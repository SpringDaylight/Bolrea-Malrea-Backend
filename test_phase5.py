"""
Phase 5 테스트: 장르별 추천 로직 확인
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.preference_helper import get_preference_for_recommendation, calculate_global
import json


def test_genre_specific_recommendation():
    """장르 명시 시: 해당 장르 특화 취향 사용"""
    print("\n" + "="*80)
    print("테스트 1: 장르 명시 - 액션 영화 추천")
    print("="*80)
    
    # 사용자 데이터
    user_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5, "긴장": 0.6, "따뜻": 0.5},
            "narrative_traits": {"성장": 0.8},
            "ending_preference": {"happy": 0.7},
            "direction_mood": {"영상미": 0.5},
            "character_relationship": {"공감": 0.7}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.3, "긴장": 0.7, "따뜻": 0.9},
                "narrative_traits": {"성장": 0.85},
                "ending_preference": {"happy": 0.8},
                "direction_mood": {"영상미": 0.6},
                "character_relationship": {"공감": 0.8}
            },
            "genres": {
                "액션": {
                    "emotion_scores": {"긴장": 0.9, "통쾌": 0.85},
                    "narrative_traits": {"전개속도": 0.9},
                    "ending_preference": {"happy": 0.9},
                    "direction_mood": {"영상미": 0.7},
                    "character_relationship": {"팀플레이": 0.8}
                },
                "드라마": {
                    "emotion_scores": {"우울": 0.3, "따뜻": 0.95},
                    "narrative_traits": {"성장": 0.9},
                    "ending_preference": {"bittersweet": 0.7},
                    "direction_mood": {"잔잔": 0.8},
                    "character_relationship": {"공감": 0.9}
                }
            },
            "review_count": 10,
            "last_updated": "2024-02-27T10:00:00Z"
        },
        "global": {
            "emotion_scores": {"우울": 0.36, "긴장": 0.67, "따뜻": 0.78},
            "narrative_traits": {"성장": 0.835},
            "ending_preference": {"happy": 0.77},
            "direction_mood": {"영상미": 0.58},
            "character_relationship": {"공감": 0.77}
        }
    }
    
    # 액션 장르 명시
    result = get_preference_for_recommendation(user_data, genre="액션")
    
    print("\n결과 (액션 특화 취향):")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증: baseline(0.6) * 0.3 + 액션리뷰(0.9) * 0.7 = 0.18 + 0.63 = 0.81
    expected_tension = 0.6 * 0.3 + 0.9 * 0.7
    assert abs(result["emotion_scores"]["긴장"] - expected_tension) < 0.01, f"긴장 계산 오류: {result['emotion_scores']['긴장']} != {expected_tension}"
    
    # 액션 리뷰에만 있는 태그 확인
    assert "통쾌" in result["emotion_scores"], "액션 특화 태그(통쾌)가 없음"
    
    print(f"\n✓ 긴장: {result['emotion_scores']['긴장']:.2f} (액션 특화)")
    print(f"✓ 통쾌: {result['emotion_scores']['통쾌']:.2f} (액션 전용 태그)")
    print("\n✅ 테스트 1 통과")
    return True


def test_no_genre_recommendation():
    """장르 명시 없음: global 사용"""
    print("\n" + "="*80)
    print("테스트 2: 장르 명시 없음 - 전체 취향 사용")
    print("="*80)
    
    user_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5, "따뜻": 0.5},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.3, "따뜻": 0.9},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            },
            "genres": {
                "액션": {"emotion_scores": {"긴장": 0.9}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}},
                "드라마": {"emotion_scores": {"우울": 0.3}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}}
            },
            "review_count": 5,
            "last_updated": "2024-02-27T10:00:00Z"
        },
        "global": {
            "emotion_scores": {"우울": 0.36, "따뜻": 0.78},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        }
    }
    
    # 장르 명시 없음
    result = get_preference_for_recommendation(user_data, genre=None)
    
    print("\n결과 (전체 취향):")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증: global과 동일해야 함
    assert result["emotion_scores"]["우울"] == 0.36, "global과 다름"
    assert result["emotion_scores"]["따뜻"] == 0.78, "global과 다름"
    
    print(f"\n✓ 우울: {result['emotion_scores']['우울']:.2f} (전체 평균)")
    print(f"✓ 따뜻: {result['emotion_scores']['따뜻']:.2f} (전체 평균)")
    print("\n✅ 테스트 2 통과")
    return True


def test_genre_not_reviewed():
    """장르 명시했지만 리뷰 없음: global 사용"""
    print("\n" + "="*80)
    print("테스트 3: 장르 명시했지만 해당 장르 리뷰 없음")
    print("="*80)
    
    user_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.3},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            },
            "genres": {
                "드라마": {"emotion_scores": {"우울": 0.3}, "narrative_traits": {}, "ending_preference": {}, "direction_mood": {}, "character_relationship": {}}
            },
            "review_count": 3,
            "last_updated": "2024-02-27T10:00:00Z"
        },
        "global": {
            "emotion_scores": {"우울": 0.36},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        }
    }
    
    # SF 장르 명시했지만 리뷰 없음
    result = get_preference_for_recommendation(user_data, genre="SF")
    
    print("\n결과 (SF 리뷰 없음 → global 사용):")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검증: global과 동일해야 함
    assert result["emotion_scores"]["우울"] == 0.36, "global로 폴백되지 않음"
    
    print(f"\n✓ SF 리뷰 없음 → global 사용")
    print(f"✓ 우울: {result['emotion_scores']['우울']:.2f}")
    print("\n✅ 테스트 3 통과")
    return True


def test_multiple_genres():
    """여러 장르 비교"""
    print("\n" + "="*80)
    print("테스트 4: 여러 장르 비교 - 액션 vs 드라마")
    print("="*80)
    
    user_data = {
        "baseline": {
            "emotion_scores": {"우울": 0.5, "긴장": 0.6, "따뜻": 0.5},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        },
        "review": {
            "global": {
                "emotion_scores": {"우울": 0.4, "긴장": 0.7, "따뜻": 0.8},
                "narrative_traits": {},
                "ending_preference": {},
                "direction_mood": {},
                "character_relationship": {}
            },
            "genres": {
                "액션": {
                    "emotion_scores": {"긴장": 0.9, "통쾌": 0.85},
                    "narrative_traits": {},
                    "ending_preference": {},
                    "direction_mood": {},
                    "character_relationship": {}
                },
                "드라마": {
                    "emotion_scores": {"우울": 0.3, "따뜻": 0.95},
                    "narrative_traits": {},
                    "ending_preference": {},
                    "direction_mood": {},
                    "character_relationship": {}
                }
            },
            "review_count": 10,
            "last_updated": "2024-02-27T10:00:00Z"
        },
        "global": {
            "emotion_scores": {"우울": 0.43, "긴장": 0.67, "따뜻": 0.71},
            "narrative_traits": {},
            "ending_preference": {},
            "direction_mood": {},
            "character_relationship": {}
        }
    }
    
    # 액션 추천
    action_pref = get_preference_for_recommendation(user_data, genre="액션")
    print("\n액션 추천 취향:")
    print(f"  긴장: {action_pref['emotion_scores'].get('긴장', 0):.2f}")
    print(f"  통쾌: {action_pref['emotion_scores'].get('통쾌', 0):.2f}")
    print(f"  따뜻: {action_pref['emotion_scores'].get('따뜻', 0):.2f}")
    
    # 드라마 추천
    drama_pref = get_preference_for_recommendation(user_data, genre="드라마")
    print("\n드라마 추천 취향:")
    print(f"  우울: {drama_pref['emotion_scores'].get('우울', 0):.2f}")
    print(f"  따뜻: {drama_pref['emotion_scores'].get('따뜻', 0):.2f}")
    print(f"  긴장: {drama_pref['emotion_scores'].get('긴장', 0):.2f}")
    
    # 검증
    assert action_pref['emotion_scores']['긴장'] > drama_pref['emotion_scores'].get('긴장', 0), "액션이 긴장감이 더 높아야 함"
    assert drama_pref['emotion_scores']['따뜻'] > action_pref['emotion_scores'].get('따뜻', 0), "드라마가 따뜻함이 더 높아야 함"
    
    print("\n✓ 액션: 긴장감 높음")
    print("✓ 드라마: 따뜻함 높음")
    print("\n✅ 테스트 4 통과")
    return True


if __name__ == "__main__":
    print("="*80)
    print("Phase 5 테스트: 장르별 추천 로직")
    print("="*80)
    
    try:
        test_genre_specific_recommendation()
        test_no_genre_recommendation()
        test_genre_not_reviewed()
        test_multiple_genres()
        
        print("\n" + "="*80)
        print("✅ 모든 테스트 통과!")
        print("="*80)
        print("\n최종 구현 완료:")
        print("1. ✅ 설문 저장: baseline 업데이트, review 보존")
        print("2. ✅ 리뷰 작성: review 누적, baseline 보존")
        print("3. ✅ global 자동 계산: baseline(30%) + review(70%)")
        print("4. ✅ 장르별 추천: 해당 장르 특화 취향 사용")
        print("5. ✅ 전체 추천: global 사용")
        print("\n다음 단계:")
        print("- 추천 API들이 genre 파라미터를 받도록 수정")
        print("- LLM이 사용자 쿼리에서 장르를 추출하도록 구현")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
