"""
실제 영화 DB 연동 - movie_vectors 테이블 사용
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from db import SessionLocal
from repositories.movie_vector import MovieVectorRepository
from models import MovieVector, Movie
import numpy as np


class MovieDBConnector:
    """실제 영화 DB와 연동 (movie_vectors 테이블)"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.repo = MovieVectorRepository(self.db)
    
    def search_movies_by_emotion(
        self,
        emotion_scores: Dict[str, float],
        top_k: int = 20,
        genres: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None
    ) -> List[Dict]:
        """
        감성 점수 기반 영화 검색
        
        Args:
            emotion_scores: 감성 점수 딕셔너리
            top_k: 상위 k개 결과
            genres: 장르 필터
            year_from: 개봉년도 시작
            year_to: 개봉년도 끝
            
        Returns:
            영화 후보 리스트
        """
        # 1. movie_vectors 테이블에서 모든 영화 가져오기
        query = self.db.query(MovieVector).join(Movie, MovieVector.movie_id == Movie.id)
        
        # 2. 연도 필터 적용
        if year_from:
            from sqlalchemy import extract
            query = query.filter(extract('year', Movie.release) >= year_from)
        if year_to:
            from sqlalchemy import extract
            query = query.filter(extract('year', Movie.release) <= year_to)
        
        movie_vectors = query.all()
        
        if not movie_vectors:
            return []
        
        # 3. 코사인 유사도 계산
        query_vector = self._emotion_scores_to_vector(emotion_scores)
        similarities = []
        
        for mv in movie_vectors:
            movie_vector = self._emotion_scores_to_vector(mv.emotion_scores)
            similarity = self._cosine_similarity(query_vector, movie_vector)
            
            # 영화 정보 조회
            movie = self.db.query(Movie).filter(Movie.id == mv.movie_id).first()
            if not movie:
                continue
            
            # 장르 필터 (있으면)
            if genres:
                movie_genres = [g.genre for g in movie.genres]
                if not any(g in movie_genres for g in genres):
                    continue
            
            similarities.append({
                "movie_id": mv.movie_id,
                "title": movie.title,
                "genres": [g.genre for g in movie.genres],
                "release_year": movie.release.year if movie.release else None,
                "similarity_score": float(similarity),
                "detail_url": f"/movies/{mv.movie_id}",
                "poster_url": movie.poster_url,
                "rating": float(movie.avg_rating) if movie.avg_rating else None,
                "emotion_profile": mv.emotion_scores,
                "narrative_profile": mv.narrative_traits
            })
        
        # 4. 유사도 순으로 정렬
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similarities[:top_k]
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        """영화 ID로 조회"""
        movie_vector = self.repo.get_by_movie_id(movie_id)
        if not movie_vector:
            return None
        
        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return None
        
        return {
            "movie_id": movie.id,
            "title": movie.title,
            "genres": [g.genre for g in movie.genres],
            "release_year": movie.release.year if movie.release else None,
            "detail_url": f"/movies/{movie.id}",
            "poster_url": movie.poster_url,
            "rating": float(movie.avg_rating) if movie.avg_rating else None,
            "synopsis": movie.synopsis,
            "emotion_profile": movie_vector.emotion_scores,
            "narrative_profile": movie_vector.narrative_traits
        }
    
    def _emotion_scores_to_vector(self, emotion_scores: Dict[str, float]) -> np.ndarray:
        """감성 점수를 벡터로 변환"""
        # 감성 태그 순서 (taxonomy와 동일하게)
        emotion_tags = [
            "우울해요", "슬퍼요", "긴장돼요", "무서워요", "설레요", 
            "로맨틱해요", "웃겨요", "밝은 분위기예요", "어두운 분위기예요",
            "잔잔해요", "현실적이에요", "몽환적이에요", "감동적이에요",
            "힐링돼요", "희망적이에요", "통쾌해요"
        ]
        
        vector = []
        for tag in emotion_tags:
            vector.append(emotion_scores.get(tag, 0.0))
        
        return np.array(vector, dtype=float)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def close(self):
        """DB 연결 종료"""
        self.db.close()

