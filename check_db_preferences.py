"""
DB에서 실제 user_preferences 데이터 확인
"""
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from utils.preference_helper import get_structure_info, is_new_structure

# DB 연결
database_url = get_database_url()
print(f"데이터베이스 연결 중...")
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("DB user_preferences 데이터 확인")
print("=" * 80)

try:
    # user_preferences 테이블 존재 확인
    result = session.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'user_preferences'
        );
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        print("\n⚠️  user_preferences 테이블이 존재하지 않습니다.")
        print("테이블을 먼저 생성해야 합니다.")
        session.close()
        exit(0)
    
    print("\n✅ user_preferences 테이블 존재 확인")
    
    # 전체 레코드 수 확인
    result = session.execute(text("SELECT COUNT(*) FROM user_preferences"))
    total_count = result.scalar()
    print(f"\n📊 전체 레코드 수: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  user_preferences 테이블이 비어있습니다.")
        print("사용자가 설문을 진행하면 데이터가 생성됩니다.")
        session.close()
        exit(0)
    
    # 최대 5개 샘플 조회
    print(f"\n📋 샘플 데이터 (최대 5개):")
    print("-" * 80)
    
    result = session.execute(text("""
        SELECT 
            id,
            user_id,
            preference_vector_json,
            persona_code,
            boost_tags,
            penalty_tags,
            updated_at
        FROM user_preferences
        LIMIT 5
    """))
    
    rows = result.fetchall()
    
    for idx, row in enumerate(rows, 1):
        print(f"\n[{idx}] User ID: {row.user_id}")
        print(f"    Persona Code: {row.persona_code}")
        print(f"    Updated At: {row.updated_at}")
        
        # preference_vector_json 분석
        pref_data = row.preference_vector_json
        
        if pref_data:
            structure_info = get_structure_info(pref_data)
            print(f"\n    📊 구조 분석:")
            print(f"       - 새 구조: {structure_info['is_new']}")
            print(f"       - 키 목록: {structure_info['keys']}")
            
            if structure_info['is_new']:
                print(f"       - baseline 존재: {structure_info['has_baseline']}")
                print(f"       - review 존재: {structure_info['has_review']}")
                print(f"       - global 존재: {structure_info['has_global']}")
                
                # 상세 정보
                if 'baseline' in pref_data:
                    baseline = pref_data['baseline']
                    print(f"\n    🎯 Baseline:")
                    if 'emotion_scores' in baseline:
                        print(f"       emotion_scores: {len(baseline['emotion_scores'])} 항목")
                    if 'narrative_traits' in baseline:
                        print(f"       narrative_traits: {len(baseline['narrative_traits'])} 항목")
                
                if 'review' in pref_data:
                    review = pref_data['review']
                    print(f"\n    📝 Review:")
                    print(f"       review_count: {review.get('review_count', 0)}")
                    print(f"       genres: {len(review.get('genres', {}))} 장르")
                    if review.get('genres'):
                        print(f"       장르 목록: {list(review['genres'].keys())}")
                
                if pref_data.get('global'):
                    print(f"\n    🌍 Global: 계산됨")
                else:
                    print(f"\n    🌍 Global: None (아직 계산 안됨)")
            else:
                print(f"       - emotion_scores 존재: {structure_info['has_emotion_scores']}")
                print(f"       - narrative_traits 존재: {structure_info['has_narrative_traits']}")
                
                # 기존 구조 상세 정보
                if 'emotion_scores' in pref_data:
                    print(f"\n    😊 Emotion Scores: {len(pref_data['emotion_scores'])} 항목")
                    # 샘플 3개만 출력
                    sample_emotions = list(pref_data['emotion_scores'].items())[:3]
                    for key, val in sample_emotions:
                        print(f"       - {key}: {val}")
                
                if 'narrative_traits' in pref_data:
                    print(f"\n    📖 Narrative Traits: {len(pref_data['narrative_traits'])} 항목")
                    sample_narratives = list(pref_data['narrative_traits'].items())[:3]
                    for key, val in sample_narratives:
                        print(f"       - {key}: {val}")
        else:
            print(f"    ⚠️  preference_vector_json이 비어있음")
        
        print("-" * 80)
    
    # 구조별 통계
    print(f"\n📈 구조별 통계:")
    result = session.execute(text("""
        SELECT 
            CASE 
                WHEN preference_vector_json ? 'baseline' THEN '새 구조'
                WHEN preference_vector_json ? 'emotion_scores' THEN '기존 구조'
                ELSE '알 수 없음'
            END as structure_type,
            COUNT(*) as count
        FROM user_preferences
        GROUP BY structure_type
    """))
    
    stats = result.fetchall()
    for stat in stats:
        print(f"   - {stat.structure_type}: {stat.count}개")
    
    print("\n" + "=" * 80)
    print("✅ DB 확인 완료")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()

print("\n다음 단계:")
print("1. 기존 구조 데이터가 있다면 정상적으로 작동하는지 확인")
print("2. Phase 2로 진행하여 마이그레이션 기능 추가")
