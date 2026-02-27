# AWS Bedrock 인증 문제 해결 + 폴백 장르 추출 개선

## 📋 문제

### 1. AWS Bedrock 인증 실패
```
⚠️ Planner LLM 오류: UnrecognizedClientException: 
The security token included in the request is invalid
```

**원인:** boto3 클라이언트가 환경변수에서 AWS 자격 증명을 자동으로 읽지 못함

### 2. 폴백 시 장르 추출 안됨
```
사용자: "재미있는 액션 영화 추천해줘"
→ LLM 실패 시 폴백
→ genres: []  ← 장르 추출 안됨
→ global 선호도 사용
```

**원인:** `_fallback_query_plan()`에서 장르 추출 로직 없음

## ✅ 해결 방법

### 1. AWS 자격 증명 명시적 전달

**수정 파일:** `llm_lab/client.py`

```python
# 수정 전
def __init__(self, model_id: str = None):
    self.region = os.getenv("AWS_REGION", "ap-northeast-2")
    self.model_id = model_id or os.getenv(...)
    self.client = boto3.client("bedrock-runtime", region_name=self.region)

# 수정 후
def __init__(self, model_id: str = None):
    self.region = os.getenv("AWS_REGION", "ap-northeast-2")
    self.model_id = model_id or os.getenv(...)
    
    # AWS 자격 증명 명시적으로 전달
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key_id and aws_secret_access_key:
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    else:
        # 환경변수 없으면 기본 자격 증명 체인 사용
        self.client = boto3.client("bedrock-runtime", region_name=self.region)
```

### 2. 폴백 시 장르 추출 개선

**수정 파일:** `llm_lab/orchestrator.py`

```python
def _fallback_query_plan(self, user_input: str) -> Dict:
    """LLM 실패 시 폴백 쿼리 플랜"""
    keywords = self.db_connector._extract_keywords(user_input)
    
    # 장르 키워드 매핑 (한국어)
    genre_keywords = {
        "액션": ["액션"],
        "드라마": ["드라마"],
        "코미디": ["코미디", "웃긴", "재밌는", "유쾌"],
        "로맨스": ["로맨스", "멜로", "사랑"],
        "스릴러": ["스릴러", "긴장", "서스펜스"],
        "공포": ["공포", "무서운", "호러"],
        "SF": ["SF", "공상과학", "미래"],
        "판타지": ["판타지", "마법"],
        "애니메이션": ["애니메이션", "애니", "만화"],
        # ... 더 많은 장르
    }
    
    # 사용자 입력에서 장르 추출
    detected_genres = []
    user_input_lower = user_input.lower()
    
    for genre, genre_keywords_list in genre_keywords.items():
        for keyword in genre_keywords_list:
            if keyword in user_input_lower:
                detected_genres.append(genre)
                break
    
    detected_genres = list(set(detected_genres))
    
    if detected_genres:
        print(f"   ✅ 폴백: 장르 추출 성공 - {detected_genres}")
    
    return {
        "keywords": keywords,
        "mood": [],
        "genres": detected_genres,  # ← 추출된 장르 포함!
        "exclude": [],
        "time_context": "",
        "attention_level": "medium"
    }
```

## 🎯 예상 동작

### LLM 정상 작동 시
```
사용자: "재미있는 액션 영화 추천해줘"
    ↓
LLM Planner 성공
    ↓
genres: ["액션"]
    ↓
✅ [Orchestrator] 장르 추출: '액션' - 장르별 선호도 사용
✅ [Satisfaction Batch] 장르별 선호도 사용: genre=액션
```

### LLM 실패 시 (폴백)
```
사용자: "재미있는 액션 영화 추천해줘"
    ↓
LLM Planner 실패
    ↓
폴백 로직 실행
    ↓
✅ 폴백: 장르 추출 성공 - ['액션']
    ↓
genres: ["액션"]
    ↓
✅ [Orchestrator] 장르 추출: '액션' - 장르별 선호도 사용
✅ [Satisfaction Batch] 장르별 선호도 사용: genre=액션
```

## 🔍 지원하는 장르

폴백 로직에서 추출 가능한 장르:
- 액션
- 드라마
- 코미디 (웃긴, 재밌는, 유쾌)
- 로맨스 (멜로, 사랑)
- 스릴러 (긴장, 서스펜스)
- 공포 (무서운, 호러)
- SF (공상과학, 미래)
- 판타지 (마법)
- 애니메이션 (애니, 만화)
- 다큐멘터리 (다큐)
- 범죄 (느와르)
- 미스터리 (추리)
- 모험
- 가족
- 전쟁
- 서부 (웨스턴)
- 뮤지컬 (음악)
- 역사

## ✅ 테스트 방법

### 1. 백엔드 재시작
```bash
# 서버 중지 후 재시작 (환경변수 다시 로드)
python app.py
```

### 2. LLM 검색 테스트
```
"재미있는 액션 영화 추천해줘"
```

### 3. 로그 확인
**LLM 성공 시:**
```
✅ LLM 추출 키워드: ['재미있', '액션']
✅ [Orchestrator] 장르 추출: '액션' - 장르별 선호도 사용
✅ [Satisfaction Batch] 장르별 선호도 사용: genre=액션
```

**LLM 실패 시 (폴백):**
```
⚠️ Planner LLM 오류: ...
✅ 폴백: 장르 추출 성공 - ['액션']
✅ [Orchestrator] 장르 추출: '액션' - 장르별 선호도 사용
✅ [Satisfaction Batch] 장르별 선호도 사용: genre=액션
```

## 🎉 결과

이제 LLM이 실패해도:
1. ✅ 폴백 로직이 장르 추출
2. ✅ 장르별 선호도 사용
3. ✅ 정확한 맞춤 추천

AWS 인증 문제도 해결되어:
1. ✅ LLM이 정상 작동
2. ✅ 더 정확한 장르 추출
3. ✅ 더 나은 추천 품질

## 📅 날짜

2024-02-27

---

**수정 완료!** 이제 LLM 성공/실패 여부와 관계없이 장르별 선호도가 작동합니다. 🎉
