"""
User Preference Updater Service
리뷰 기반으로 사용자 취향을 업데이트하는 서비스
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from repositories.user_preference import UserPreferenceRepository
from repositories.movie_vector import MovieVectorRepository


class PreferenceUpdater:
    """리뷰 기반 취향 업데이트 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_pref_repo = UserPreferenceRepository(db)
        self.movie_vector_repo = MovieVectorRepository(db)
    
    def update_from_review(
        self,
        user_id: str,
        movie_id: int,
        rating: float,
        learning_rate: float = 0.15
    ) -> Dict[str, Any]:
        """
        리뷰 기반으로 사용자 취향 업데이트
        
        Args:
            user_id: 사용자 ID
            movie_id: 영화 ID
            rating: 평점 (0.5~5.0)
            learning_rate: 학습률 (기본 0.15, 높을수록 빠르게 변화)
        
        Returns:
            업데이트된 취향 데이터
        """
        # 1. 기존 사용자 취향 가져오기
        user_pref = self.user_pref_repo.get_by_user_id(user_id)
        if not user_pref:
            return {
                "success": False,
                "message": "User preference not found. Please complete taste survey first."
            }
        
        # 2. 영화 벡터 가져오기
        movie_vector = self.movie_vector_repo.get_by_movie_id(movie_id)
        if not movie_vector:
            return {
                "success": False,
                "message": "Movie vector not found. Cannot update preference."
            }
        
        # 3. 평점을 가중치로 변환 (0.5~5.0 -> -0.5~1.0)
        # 3.0 이상: 긍정적 영향, 3.0 미만: 부정적 영향
        weight = (rating - 3.0) / 2.0  # -1.25~1.0 범위
        weight = max(-0.5, min(1.0, weight))  # -0.5~1.0으로 클립
        
        # 4. 기존 취향 벡터 업데이트 (가중 평균)
        current_pref = user_pref.preference_vector_json
        
        updated_pref = {
            "emotion_scores": self._update_vector(
                current_pref.get("emotion_scores", {}),
                movie_vector.emotion_scores,
                weight,
                learning_rate
            ),
            "narrative_traits": self._update_vector(
                current_pref.get("narrative_traits", {}),
                movie_vector.narrative_traits,
                weight,
                learning_rate
            ),
            "direction_mood": self._update_vector(
                current_pref.get("direction_mood", {}),
                movie_vector.direction_mood,
                weight,
                learning_rate
            ),
            "character_relationship": self._update_vector(
                current_pref.get("character_relationship", {}),
                movie_vector.character_relationship,
                weight,
                learning_rate
            ),
            "ending_preference": self._update_vector(
                current_pref.get("ending_preference", {}),
                movie_vector.ending_preference,
                weight,
                learning_rate
            )
        }
        
        # 5. boost_tags와 dislike_tags 업데이트
        boost_tags = list(user_pref.boost_tags) if user_pref.boost_tags else []
        dislike_tags = list(user_pref.dislike_tags) if user_pref.dislike_tags else []
        
        # 높은 평점(4.0 이상)이면 영화의 주요 태그를 boost_tags에 추가
        if rating >= 4.0:
            top_tags = self._get_top_tags(movie_vector, limit=3)
            for tag in top_tags:
                if tag not in boost_tags and tag not in dislike_tags:
                    boost_tags.append(tag)
            # 최대 20개로 제한
            boost_tags = boost_tags[-20:]
        
        # 낮은 평점(2.0 이하)이면 영화의 주요 태그를 dislike_tags에 추가
        elif rating <= 2.0:
            top_tags = self._get_top_tags(movie_vector, limit=2)
            for tag in top_tags:
                if tag not in dislike_tags and tag not in boost_tags:
                    dislike_tags.append(tag)
            # 최대 15개로 제한
            dislike_tags = dislike_tags[-15:]
        
        # 6. DB에 저장
        updated = self.user_pref_repo.upsert(
            user_id=user_id,
            preference_vector_json=updated_pref,
            persona_code=user_pref.persona_code,
            boost_tags=boost_tags,
            dislike_tags=dislike_tags,
            penalty_tags=list(user_pref.penalty_tags) if user_pref.penalty_tags else []
        )
        
        return {
            "success": True,
            "message": "User preference updated based on review",
            "user_id": user_id,
            "movie_id": movie_id,
            "rating": rating,
            "weight": weight,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None
        }
    
    def _update_vector(
        self,
        current: Dict[str, float],
        movie: Dict[str, float],
        weight: float,
        learning_rate: float
    ) -> Dict[str, float]:
        """
        벡터 업데이트 (가중 평균)
        
        new_value = current_value + learning_rate * weight * (movie_value - current_value)
        """
        updated = {}
        all_keys = set(current.keys()) | set(movie.keys())
        
        for key in all_keys:
            current_val = current.get(key, 0.0)
            movie_val = movie.get(key, 0.0)
            
            # 가중 평균 업데이트
            if weight > 0:
                # 긍정적 평가: 영화 특성 쪽으로 이동
                delta = learning_rate * weight * (movie_val - current_val)
            else:
                # 부정적 평가: 영화 특성 반대 방향으로 이동
                delta = learning_rate * weight * movie_val
            
            new_val = current_val + delta
            # 0~1 범위로 클립
            new_val = max(0.0, min(1.0, new_val))
            
            updated[key] = round(new_val, 3)
        
        return updated
    
    def _get_top_tags(self, movie_vector, limit: int = 3) -> list:
        """영화의 주요 태그 추출"""
        all_scores = {}
        
        # 모든 카테고리에서 점수 수집
        for category in ['emotion_scores', 'narrative_traits', 'direction_mood', 'character_relationship']:
            scores = getattr(movie_vector, category, {})
            if isinstance(scores, dict):
                all_scores.update(scores)
        
        # 점수 높은 순으로 정렬
        sorted_tags = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 N개 태그 반환
        return [tag for tag, score in sorted_tags[:limit] if score > 0.3]
