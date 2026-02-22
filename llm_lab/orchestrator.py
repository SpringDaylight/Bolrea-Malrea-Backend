"""
LLM Orchestrator - LLM을 컨트롤러로 사용하는 추천 시스템

아키텍처:
1. Planner LLM: 사용자 요청 분석 → 구조화된 쿼리
2. Multi-source Retrieval: 키워드 검색 + 벡터 검색 + (외부 검색)
3. Candidate Pooling: 후보 합치기 + 필터링
4. Ranker LLM: 재랭킹 + 설명 생성
5. ID Validation: 할루시네이션 방지
"""
from typing import List, Dict, Optional, Set
import json
from llm_lab.client import LLMClient
from llm_lab.movie_db_connector import MovieDBConnector
from domain.a5_emotional_search import emotional_search


class LLMOrchestrator:
    """
    LLM 기반 영화 추천 오케스트레이터
    
    핵심 원칙:
    - LLM은 '결정권'을 가짐
    - '사실/존재성'은 시스템이 강제 검증
    - 후보는 항상 검증된 소스에서만
    """
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.db_connector = MovieDBConnector()
    
    def recommend(
        self,
        user_input: str,
        top_k: int = 5,
        candidate_pool_size: int = 150
    ) -> Dict:
        """
        LLM 오케스트레이션 기반 추천
        
        Args:
            user_input: 사용자 입력
            top_k: 최종 추천 개수
            candidate_pool_size: 후보 풀 크기
            
        Returns:
            추천 결과 (영화 리스트 + 설명)
        """
        # Step 1: Planner LLM - 요청 분석
        query_plan = self._plan_query(user_input)
        
        # Step 2: Multi-source Retrieval
        candidates = self._retrieve_candidates(
            user_input=user_input,
            query_plan=query_plan,
            pool_size=candidate_pool_size
        )
        
        if not candidates:
            return {
                "recommendations": [],
                "explanation": "죄송합니다. 조건에 맞는 영화를 찾을 수 없습니다.",
                "candidates_count": 0
            }
        
        # Step 3: Ranker LLM - 재랭킹 + 설명
        ranked_results = self._rank_and_explain(
            user_input=user_input,
            candidates=candidates,
            top_k=top_k
        )
        
        # Step 4: ID Validation - 할루시네이션 방지
        validated_results = self._validate_recommendations(
            ranked_results=ranked_results,
            candidate_pool=candidates
        )
        
        return validated_results
    
    def _plan_query(self, user_input: str) -> Dict:
        """
        Step 1: Planner LLM - 사용자 요청을 구조화된 쿼리로 변환
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            구조화된 쿼리 (키워드, 감성, 필터 등)
        """
        planner_prompt = f"""사용자의 영화 추천 요청을 분석하여 구조화된 검색 쿼리를 생성하세요.

사용자 요청: "{user_input}"

다음 형식의 JSON으로 응답하세요:
{{
    "keywords": ["키워드1", "키워드2"],  // 주제, 소재, 등장인물 등
    "mood": ["분위기1", "분위기2"],      // 우울한, 힐링, 긴장감 등
    "genres": ["장르1", "장르2"],        // 드라마, 로맨스, 액션 등
    "exclude": ["제외할_요소"],          // 너무 잔혹한, 복잡한 등
    "time_context": "시간대",            // 밤, 주말, 비오는날 등
    "attention_level": "집중도"          // high, medium, low
}}

JSON만 출력하세요:"""

        try:
            response = self.llm_client.generate_simple(planner_prompt)
            
            # JSON 추출
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                query_plan = json.loads(json_str)
                return query_plan
            else:
                # JSON 파싱 실패 시 기본값
                return self._fallback_query_plan(user_input)
                
        except Exception as e:
            print(f"⚠️ Planner LLM 오류: {e}")
            return self._fallback_query_plan(user_input)
    
    def _fallback_query_plan(self, user_input: str) -> Dict:
        """LLM 실패 시 폴백 쿼리 플랜"""
        # 간단한 키워드 추출
        keywords = self.db_connector._extract_keywords(user_input)
        
        return {
            "keywords": keywords,
            "mood": [],
            "genres": [],
            "exclude": [],
            "time_context": "",
            "attention_level": "medium"
        }
    
    def _retrieve_candidates(
        self,
        user_input: str,
        query_plan: Dict,
        pool_size: int
    ) -> List[Dict]:
        """
        Step 2: Multi-source Retrieval
        
        소스:
        1. 키워드 검색 (제목, 시놉시스, 등장인물)
        2. 벡터 검색 (감성 유사도)
        3. (선택) 외부 검색
        
        Args:
            user_input: 사용자 입력
            query_plan: 구조화된 쿼리
            pool_size: 후보 풀 크기
            
        Returns:
            후보 영화 리스트
        """
        all_candidates = {}  # movie_id -> movie_info
        
        # 쿼리 유형 분석 및 가중치 결정
        keyword_weight, emotion_weight = self._determine_weights(
            user_input=user_input,
            query_plan=query_plan
        )
        
        print(f"🎯 가중치 결정: 키워드={keyword_weight:.1f}, 감성={emotion_weight:.1f}")
        
        # Source 1: 키워드 검색 (하이브리드 검색 활용)
        try:
            # 감성 분석
            search_result = emotional_search({"text": user_input})
            emotion_scores = search_result["expanded_query"]["emotion_scores"]
            
            # 하이브리드 검색 (동적 가중치 적용)
            keyword_results = self.db_connector.search_movies_hybrid(
                user_input=user_input,
                emotion_scores=emotion_scores,
                top_k=pool_size,
                genres=query_plan.get("genres"),
                keyword_weight=keyword_weight,  # 동적 가중치
                emotion_weight=emotion_weight   # 동적 가중치
            )
            
            for movie in keyword_results:
                movie_id = movie['movie_id']
                if movie_id not in all_candidates:
                    all_candidates[movie_id] = movie
                    all_candidates[movie_id]['sources'] = []
                all_candidates[movie_id]['sources'].append('keyword')
                
        except Exception as e:
            print(f"⚠️ 키워드 검색 오류: {e}")
        
        # Source 2: 벡터 검색 (감성 기반)
        try:
            vector_results = self.db_connector.search_movies_by_emotion(
                emotion_scores=emotion_scores,
                top_k=pool_size,
                genres=query_plan.get("genres")
            )
            
            for movie in vector_results:
                movie_id = movie['movie_id']
                if movie_id not in all_candidates:
                    all_candidates[movie_id] = movie
                    all_candidates[movie_id]['sources'] = []
                all_candidates[movie_id]['sources'].append('vector')
                
        except Exception as e:
            print(f"⚠️ 벡터 검색 오류: {e}")
        
        # 후보 리스트로 변환
        candidates = list(all_candidates.values())
        
        # 다중 소스에서 발견된 영화 우선순위
        candidates.sort(key=lambda x: len(x.get('sources', [])), reverse=True)
        
        return candidates[:pool_size]
    
    def _determine_weights(
        self,
        user_input: str,
        query_plan: Dict
    ) -> tuple[float, float]:
        """
        쿼리 유형 분석 및 가중치 결정
        
        Args:
            user_input: 사용자 입력
            query_plan: 구조화된 쿼리
            
        Returns:
            (keyword_weight, emotion_weight) 튜플
        """
        # 1. 키워드 개수 확인
        keywords = query_plan.get("keywords", [])
        keyword_count = len(keywords)
        
        # 2. 감성 단어 개수 확인
        mood_words = query_plan.get("mood", [])
        mood_count = len(mood_words)
        
        # 3. 감성 키워드 리스트 (한국어)
        emotion_keywords = {
            '우울', '슬픈', '슬프', '힐링', '따뜻', '감동', '설레', '로맨틱',
            '무서', '긴장', '스릴', '웃긴', '재미', '유쾌', '밝은', '어두운',
            '잔잔', '몽환', '희망', '통쾌', '소름', '현실', '멜로', '코미디'
        }
        
        # 4. 입력에서 감성 키워드 찾기
        emotion_word_count = sum(
            1 for word in emotion_keywords 
            if word in user_input
        )
        
        # 5. 주제/키워드 단어 리스트 (한국어)
        topic_keywords = {
            '직장', '상사', '학교', '선생', '가족', '부모', '친구', '연인',
            '전쟁', '역사', '정치', '범죄', '의사', '경찰', '군인', '요리',
            '음악', '춤', '스포츠', '게임', '여행', '우주', '좀비', '로봇',
            '마법', '판타지', '시간여행', '평행우주', '복수', '성장', '사랑'
        }
        
        # 6. 입력에서 주제 키워드 찾기
        topic_word_count = sum(
            1 for word in topic_keywords 
            if word in user_input
        )
        
        # 7. 가중치 결정 로직
        
        # 케이스 1: 주제 키워드가 많고 감성 키워드가 적음 → 키워드 중심
        if topic_word_count >= 2 and emotion_word_count == 0:
            return (0.9, 0.1)  # 키워드 90%
        
        if topic_word_count >= 1 and emotion_word_count == 0:
            return (0.8, 0.2)  # 키워드 80%
        
        # 케이스 2: 감성 키워드가 많고 주제 키워드가 적음 → 감성 중심
        if emotion_word_count >= 2 and topic_word_count == 0:
            return (0.2, 0.8)  # 감성 80%
        
        if emotion_word_count >= 1 and topic_word_count == 0:
            return (0.3, 0.7)  # 감성 70%
        
        # 케이스 3: 둘 다 있음 → 균형
        if topic_word_count >= 1 and emotion_word_count >= 1:
            return (0.5, 0.5)  # 균형 50:50
        
        # 케이스 4: 둘 다 없음 (일반적인 쿼리) → 약간 키워드 우선
        return (0.6, 0.4)  # 키워드 60%
    
    def _rank_and_explain(
        self,
        user_input: str,
        candidates: List[Dict],
        top_k: int
    ) -> Dict:
        """
        Step 3: Ranker LLM - 후보 재랭킹 + 설명 생성
        
        Args:
            user_input: 사용자 입력
            candidates: 후보 영화 리스트
            top_k: 최종 추천 개수
            
        Returns:
            랭킹 결과 (영화 ID + 설명)
        """
        # 후보 포맷팅 (LLM이 읽을 수 있게)
        candidates_text = self._format_candidates_for_ranking(candidates)
        
        ranker_prompt = f"""당신은 영화 추천 전문가입니다. 사용자의 요청에 가장 적합한 영화를 선택하고 이유를 설명하세요.

사용자 요청: "{user_input}"

후보 영화 목록:
{candidates_text}

⚠️ 중요 규칙:
1. 반드시 위 목록의 영화 ID만 사용하세요
2. 목록에 없는 영화는 절대 추천하지 마세요
3. 상위 {top_k}개를 선택하세요

다음 형식의 JSON으로 응답하세요:
{{
    "selected_movie_ids": [123, 456, 789],
    "explanation": "전체 추천 이유 (2-3문장)",
    "individual_reasons": {{
        "123": "이 영화를 추천하는 이유",
        "456": "이 영화를 추천하는 이유",
        "789": "이 영화를 추천하는 이유"
    }}
}}

JSON만 출력하세요:"""

        try:
            response = self.llm_client.generate_simple(ranker_prompt)
            
            # JSON 추출
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                ranking_result = json.loads(json_str)
                return ranking_result
            else:
                # JSON 파싱 실패 시 폴백
                return self._fallback_ranking(candidates, top_k)
                
        except Exception as e:
            print(f"⚠️ Ranker LLM 오류: {e}")
            return self._fallback_ranking(candidates, top_k)
    
    def _format_candidates_for_ranking(self, candidates: List[Dict]) -> str:
        """후보를 LLM이 읽을 수 있는 형식으로 변환"""
        lines = []
        for i, movie in enumerate(candidates[:50], 1):  # 최대 50개만 (토큰 제한)
            lines.append(f"{i}. [ID: {movie['movie_id']}] {movie['title']}")
            lines.append(f"   장르: {', '.join(movie.get('genres', []))}")
            lines.append(f"   개봉: {movie.get('release_year', 'N/A')}")
            
            # 시놉시스 (있으면)
            if movie.get('synopsis'):
                synopsis = movie['synopsis'][:150]  # 150자로 제한
                lines.append(f"   줄거리: {synopsis}...")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _fallback_ranking(self, candidates: List[Dict], top_k: int) -> Dict:
        """LLM 실패 시 폴백 랭킹 (유사도 기반)"""
        top_candidates = candidates[:top_k]
        
        return {
            "selected_movie_ids": [m['movie_id'] for m in top_candidates],
            "explanation": "추천 영화를 선별했습니다.",
            "individual_reasons": {
                str(m['movie_id']): f"{m['title']}을(를) 추천합니다."
                for m in top_candidates
            }
        }
    
    def _validate_recommendations(
        self,
        ranked_results: Dict,
        candidate_pool: List[Dict]
    ) -> Dict:
        """
        Step 4: ID Validation - 할루시네이션 방지
        
        Args:
            ranked_results: LLM 랭킹 결과
            candidate_pool: 원본 후보 풀
            
        Returns:
            검증된 추천 결과
        """
        # 후보 풀의 ID 집합
        valid_ids = {m['movie_id'] for m in candidate_pool}
        
        # LLM이 선택한 ID
        selected_ids = ranked_results.get('selected_movie_ids', [])
        
        # ID 검증
        validated_ids = [mid for mid in selected_ids if mid in valid_ids]
        
        if len(validated_ids) < len(selected_ids):
            print(f"⚠️ 할루시네이션 감지: {len(selected_ids) - len(validated_ids)}개 영화 제외됨")
        
        # 검증된 영화 정보 조회
        id_to_movie = {m['movie_id']: m for m in candidate_pool}
        
        recommendations = []
        for movie_id in validated_ids:
            movie = id_to_movie[movie_id]
            reason = ranked_results.get('individual_reasons', {}).get(str(movie_id), "")
            
            recommendations.append({
                "movie_id": movie['movie_id'],
                "title": movie['title'],
                "genres": movie.get('genres', []),
                "release_year": movie.get('release_year'),
                "similarity_score": movie.get('similarity_score', 0),
                "detail_url": movie.get('detail_url'),
                "poster_url": movie.get('poster_url'),
                "rating": movie.get('rating'),
                "reason": reason  # LLM이 생성한 개별 이유
            })
        
        return {
            "recommendations": recommendations,
            "explanation": ranked_results.get('explanation', ''),
            "candidates_count": len(candidate_pool),
            "validated": True
        }
    
    def close(self):
        """리소스 정리"""
        self.db_connector.close()
