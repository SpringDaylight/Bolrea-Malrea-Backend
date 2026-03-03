"""
Phase 2: preference_vector_json 마이그레이션 스크립트

기존 구조 또는 불완전한 구조를 완전한 새 구조로 변환:
{
  "baseline": {...},
  "review": {
    "global": {...},
    "genres": {...},
    "review_count": 0
  },
  "global": null
}
"""
import sys
import os

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from utils.preference_helper import is_new_structure, migrate_to_new_structure

def migrate_single_user(session, user_id: str, dry_run: bool = True):
    """단일 사용자 마이그레이션"""
    
    # 현재 데이터 조회
    result = session.execute(
        text("SELECT preference_vector_json FROM user_preferences WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        print(f"❌ User {user_id} not found")
        return False
    
    old_data = row[0]
    
    if not old_data:
        print(f"⚠️  User {user_id}: preference_vector_json is empty")
        return False
    
    # 구조 확인
    print(f"\n{'='*80}")
    print(f"User: {user_id}")
    print(f"{'='*80}")
    print(f"현재 키: {list(old_data.keys())}")
    
    # 이미 완전한 새 구조인지 확인
    has_baseline = 'baseline' in old_data
    has_review = 'review' in old_data
    has_global_key = 'global' in old_data
    
    if has_baseline and has_review and has_global_key:
        print(f"✅ 이미 완전한 새 구조입니다. 마이그레이션 불필요.")
        return False
    
    # 마이그레이션 수행
    print(f"\n🔄 마이그레이션 시작...")
    
    # 1. 기존 구조 (emotion_scores 등이 최상위에 있음)
    if 'emotion_scores' in old_data or 'narrative_traits' in old_data:
        print(f"   타입: 기존 구조 → 새 구조")
        new_data = {
            "baseline": {},
            "review": {
                "global": {},
                "genres": {},
                "review_count": 0,
                "last_updated": None
            },
            "global": None
        }
        
        # 모든 카테고리를 baseline으로 이동
        for key in ['emotion_scores', 'narrative_traits', 'ending_preference', 
                    'direction_mood', 'character_relationship']:
            if key in old_data:
                new_data["baseline"][key] = old_data[key]
                print(f"   ✓ {key} → baseline")
    
    # 2. 불완전한 새 구조 (genres/global만 있음)
    elif 'genres' in old_data and 'global' in old_data:
        print(f"   타입: 불완전한 구조 → 완전한 새 구조")
        new_data = {
            "baseline": {},
            "review": {
                "global": {},
                "genres": old_data.get('genres', {}),
                "review_count": len(old_data.get('genres', {})),
                "last_updated": None
            },
            "global": old_data.get('global')
        }
        print(f"   ✓ genres → review.genres ({len(old_data.get('genres', {}))}개 장르)")
        print(f"   ✓ global → global")
        print(f"   ⚠️  baseline은 비어있음 (설문 필요)")
    
    else:
        print(f"❌ 알 수 없는 구조: {list(old_data.keys())}")
        return False
    
    # 결과 출력
    print(f"\n📊 마이그레이션 결과:")
    print(f"   - baseline: {'있음' if new_data['baseline'] else '비어있음'}")
    print(f"   - review.genres: {len(new_data['review']['genres'])}개")
    print(f"   - review.review_count: {new_data['review']['review_count']}")
    print(f"   - global: {'계산됨' if new_data['global'] else 'None'}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN 모드: 실제 DB 업데이트 안함")
        return True
    
    # 실제 업데이트
    try:
        import json
        session.execute(
            text("""
                UPDATE user_preferences 
                SET preference_vector_json = CAST(:new_data AS jsonb)
                WHERE user_id = :user_id
            """),
            {"new_data": json.dumps(new_data), "user_id": user_id}
        )
        session.commit()
        print(f"\n✅ DB 업데이트 완료")
        return True
    except Exception as e:
        session.rollback()
        print(f"\n❌ DB 업데이트 실패: {e}")
        return False


def migrate_all_users(dry_run: bool = True):
    """모든 사용자 마이그레이션"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 마이그레이션 필요한 사용자 조회
        result = session.execute(text("""
            SELECT user_id, preference_vector_json
            FROM user_preferences
            WHERE preference_vector_json IS NOT NULL
        """))
        
        rows = result.fetchall()
        total = len(rows)
        
        print(f"{'='*80}")
        print(f"전체 마이그레이션 {'(DRY RUN)' if dry_run else '(실제 실행)'}")
        print(f"{'='*80}")
        print(f"총 {total}개 레코드 확인 중...\n")
        
        need_migration = []
        already_migrated = []
        
        for row in rows:
            user_id = row[0]
            data = row[1]
            
            has_baseline = 'baseline' in data
            has_review = 'review' in data
            has_global = 'global' in data
            
            if has_baseline and has_review and has_global:
                already_migrated.append(user_id)
            else:
                need_migration.append(user_id)
        
        print(f"📊 통계:")
        print(f"   - 이미 마이그레이션됨: {len(already_migrated)}개")
        print(f"   - 마이그레이션 필요: {len(need_migration)}개")
        
        if len(need_migration) == 0:
            print(f"\n✅ 모든 데이터가 이미 마이그레이션되었습니다!")
            return
        
        print(f"\n{'='*80}")
        print(f"마이그레이션 시작...")
        print(f"{'='*80}")
        
        success_count = 0
        fail_count = 0
        
        for idx, user_id in enumerate(need_migration, 1):
            print(f"\n[{idx}/{len(need_migration)}] {user_id}")
            print(f"-" * 80)
            
            if migrate_single_user(session, user_id, dry_run=dry_run):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n{'='*80}")
        print(f"마이그레이션 완료")
        print(f"{'='*80}")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패/스킵: {fail_count}개")
        
        if dry_run:
            print(f"\n⚠️  DRY RUN 모드였습니다. 실제 DB는 변경되지 않았습니다.")
            print(f"실제 마이그레이션을 실행하려면: python scripts/migrate_preferences.py --execute")
        
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Preference Vector 마이그레이션")
    parser.add_argument("--user-id", help="특정 사용자만 마이그레이션")
    parser.add_argument("--execute", action="store_true", help="실제 DB 업데이트 (기본은 dry-run)")
    parser.add_argument("--all", action="store_true", help="모든 사용자 마이그레이션")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if args.user_id:
        # 단일 사용자 마이그레이션
        database_url = get_database_url()
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            migrate_single_user(session, args.user_id, dry_run=dry_run)
        finally:
            session.close()
    
    elif args.all:
        # 전체 마이그레이션
        migrate_all_users(dry_run=dry_run)
    
    else:
        print("사용법:")
        print("  단일 사용자: python scripts/migrate_preferences.py --user-id USER_ID [--execute]")
        print("  전체 사용자: python scripts/migrate_preferences.py --all [--execute]")
        print("")
        print("옵션:")
        print("  --execute: 실제 DB 업데이트 (없으면 dry-run)")
