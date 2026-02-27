"""
DB 데이터 상세 확인 - JSON 전체 출력
"""
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import get_database_url

database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("preference_vector_json 상세 내용 확인")
print("=" * 80)

try:
    # 각 구조 타입별로 1개씩 샘플 조회
    
    # 1. 기존 구조 (emotion_scores 있음)
    print("\n[1] 기존 구조 샘플:")
    print("-" * 80)
    result = session.execute(text("""
        SELECT user_id, preference_vector_json
        FROM user_preferences
        WHERE preference_vector_json ? 'emotion_scores'
        LIMIT 1
    """))
    row = result.fetchone()
    if row:
        print(f"User ID: {row.user_id}")
        print(f"\nJSON 내용:")
        print(json.dumps(row.preference_vector_json, indent=2, ensure_ascii=False))
    else:
        print("기존 구조 데이터 없음")
    
    # 2. 새 구조 (baseline 있음)
    print("\n\n[2] 새 구조 (baseline 있음) 샘플:")
    print("-" * 80)
    result = session.execute(text("""
        SELECT user_id, preference_vector_json
        FROM user_preferences
        WHERE preference_vector_json ? 'baseline'
        LIMIT 1
    """))
    row = result.fetchone()
    if row:
        print(f"User ID: {row.user_id}")
        print(f"\nJSON 내용:")
        print(json.dumps(row.preference_vector_json, indent=2, ensure_ascii=False))
    else:
        print("baseline 있는 데이터 없음")
    
    # 3. genres/global만 있는 구조
    print("\n\n[3] genres/global 구조 샘플:")
    print("-" * 80)
    result = session.execute(text("""
        SELECT user_id, preference_vector_json
        FROM user_preferences
        WHERE preference_vector_json ? 'genres'
        AND NOT preference_vector_json ? 'baseline'
        AND NOT preference_vector_json ? 'emotion_scores'
        LIMIT 1
    """))
    row = result.fetchone()
    if row:
        print(f"User ID: {row.user_id}")
        print(f"\nJSON 내용:")
        print(json.dumps(row.preference_vector_json, indent=2, ensure_ascii=False))
    else:
        print("genres/global 구조 데이터 없음")
    
    # 4. 알 수 없는 구조
    print("\n\n[4] 알 수 없는 구조 샘플:")
    print("-" * 80)
    result = session.execute(text("""
        SELECT user_id, preference_vector_json
        FROM user_preferences
        WHERE NOT preference_vector_json ? 'baseline'
        AND NOT preference_vector_json ? 'emotion_scores'
        AND NOT preference_vector_json ? 'genres'
        LIMIT 1
    """))
    row = result.fetchone()
    if row:
        print(f"User ID: {row.user_id}")
        print(f"\nJSON 내용:")
        print(json.dumps(row.preference_vector_json, indent=2, ensure_ascii=False))
    else:
        print("알 수 없는 구조 데이터 없음")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
