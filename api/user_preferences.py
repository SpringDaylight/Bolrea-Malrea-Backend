"""
User Preferences API
Endpoints for saving and retrieving user taste preferences
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import io

from db import get_db
from repositories.user_preference import UserPreferenceRepository
from schemas import UserPreferenceResponse, MessageResponse
from pydantic import BaseModel, Field

try:
    from wordcloud import WordCloud
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False


router = APIRouter(prefix="/api/user-preferences", tags=["User Preferences"])


# ============================================
# Request Schemas
# ============================================

class SaveUserPreferenceRequest(BaseModel):
    """Request schema for saving user preference"""
    user_id: str = Field(..., description="User ID")
    preference_vector_json: Dict[str, Any] = Field(
        ...,
        description="Preference vector containing emotion_scores, narrative_traits, direction_mood, character_relationship, ending_preference"
    )
    persona_code: Optional[str] = Field(None, description="User persona code")
    boost_tags: List[str] = Field(default_factory=list, description="List of liked tags")
    dislike_tags: List[str] = Field(default_factory=list, description="List of disliked tags")
    penalty_tags: List[str] = Field(default_factory=list, description="List of penalty tags")


# ============================================
# Endpoints
# ============================================

@router.get("/{user_id}", response_model=UserPreferenceResponse)
def get_user_preference(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user preference by user_id
    
    Returns the saved user taste preference including:
    - preference_vector_json: emotion_scores, narrative_traits, etc.
    - boost_tags: liked tags
    - dislike_tags: disliked tags
    - penalty_tags: penalty tags
    """
    repo = UserPreferenceRepository(db)
    preference = repo.get_by_user_id(user_id)
    
    if not preference:
        raise HTTPException(
            status_code=404,
            detail=f"User preference not found for user_id: {user_id}"
        )
    
    return UserPreferenceResponse(
        user_id=preference.user_id,
        preference_vector_json=preference.preference_vector_json,
        persona_code=preference.persona_code,
        boost_tags=preference.boost_tags,
        penalty_tags=preference.penalty_tags,
        updated_at=preference.updated_at
    )


@router.post("", response_model=UserPreferenceResponse, status_code=201)
def save_user_preference(
    request: SaveUserPreferenceRequest,
    db: Session = Depends(get_db)
):
    """
    Save or update user preference (upsert)
    
    If preference exists for the user, it will be updated.
    Otherwise, a new preference will be created.
    
    Request body should include:
    - user_id: User identifier
    - preference_vector_json: Complete preference vector
    - boost_tags: List of liked tags (optional)
    - dislike_tags: List of disliked tags (optional)
    - penalty_tags: List of penalty tags (optional)
    """
    repo = UserPreferenceRepository(db)
    
    preference = repo.upsert(
        user_id=request.user_id,
        preference_vector_json=request.preference_vector_json,
        persona_code=request.persona_code,
        boost_tags=request.boost_tags,
        dislike_tags=request.dislike_tags,
        penalty_tags=request.penalty_tags
    )
    
    return UserPreferenceResponse(
        user_id=preference.user_id,
        preference_vector_json=preference.preference_vector_json,
        persona_code=preference.persona_code,
        boost_tags=preference.boost_tags,
        penalty_tags=preference.penalty_tags,
        updated_at=preference.updated_at
    )


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user_preference(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete user preference by user_id
    """
    repo = UserPreferenceRepository(db)
    
    if not repo.exists(user_id):
        raise HTTPException(
            status_code=404,
            detail=f"User preference not found for user_id: {user_id}"
        )
    
    success = repo.delete_by_user_id(user_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user preference"
        )
    
    return MessageResponse(message=f"User preference deleted for user_id: {user_id}")


@router.get("/{user_id}/exists")
def check_user_preference_exists(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if user preference exists
    """
    repo = UserPreferenceRepository(db)
    exists = repo.exists(user_id)
    
    return {
        "user_id": user_id,
        "exists": exists
    }


@router.post("/{user_id}/update-from-review", response_model=dict)
def update_preference_from_review(
    user_id: str,
    movie_id: int = Query(..., description="Movie ID"),
    rating: float = Query(..., ge=0.5, le=5.0, description="Rating (0.5~5.0)"),
    review_text: Optional[str] = Query(None, description="Review text (optional)"),
    learning_rate: float = Query(0.15, ge=0.01, le=0.5, description="Learning rate (0.01~0.5)"),
    db: Session = Depends(get_db)
):
    """
    Update user preference based on review
    
    리뷰 작성 시 자동으로 호출되어 사용자 취향을 업데이트합니다.
    
    Parameters:
    - user_id: User ID
    - movie_id: Movie ID
    - rating: Review rating (0.5~5.0)
    - review_text: Review text (optional, for movie vector update)
    - learning_rate: How much to adjust preference (default: 0.15)
    
    Returns:
    - success: Whether update was successful
    - message: Status message
    - updated_at: Timestamp of update
    """
    from services.preference_updater import PreferenceUpdater
    
    updater = PreferenceUpdater(db)
    result = updater.update_from_review(
        user_id=user_id,
        movie_id=movie_id,
        rating=rating,
        review_text=review_text,
        learning_rate=learning_rate
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to update preference")
        )
    
    return result


@router.get("/{user_id}/wordcloud")
def get_user_wordcloud(
    user_id: str,
    type: str = "both",
    db: Session = Depends(get_db)
):
    """
    Generate and return a word cloud image for the user's taste tags.
    type: 'boost' (liked), 'dislike' (disliked), 'both'
    """
    if not HAS_WORDCLOUD:
        raise HTTPException(
            status_code=501,
            detail="wordcloud / matplotlib not installed. Run: pip install wordcloud matplotlib"
        )

    repo = UserPreferenceRepository(db)
    preference = repo.get_by_user_id(user_id)

    if not preference:
        raise HTTPException(status_code=404, detail=f"No preference found for user {user_id}")

    boost_tags: list = preference.boost_tags or []
    pref_vector = preference.preference_vector_json or {}
    # emotion_scores: {"감동적이에요": 0.85, ...}
    emotion_scores: dict = pref_vector.get("emotion_scores", {})

    FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

    def make_wc_from_freq(freq: dict, colormap: str, width=600, height=400):
        """주파수 딕셔너리로 워드클라우드 생성"""
        return WordCloud(
            font_path=FONT_PATH,
            width=width,
            height=height,
            background_color="white",
            colormap=colormap,
            relative_scaling=0.5,
            min_font_size=10,
        ).generate_from_frequencies(freq)

    def make_wc_from_list(tags: list, colormap: str, width=600, height=400):
        """태그 리스트로 워드클라우드 생성 (앞쪽 태그일수록 가중치 높음)"""
        freq = {tag: (len(tags) - i) for i, tag in enumerate(tags)}
        return make_wc_from_freq(freq, colormap, width, height)

    from matplotlib.font_manager import FontProperties
    fp = FontProperties(fname=FONT_PATH)

    fig, ax = None, None

    if type == "boost":
        if not boost_tags:
            raise HTTPException(status_code=404, detail="No boost tags found")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(make_wc_from_list(boost_tags, "Blues"), interpolation="bilinear")
        ax.axis("off")
    elif type == "dislike":
        raise HTTPException(status_code=400, detail="dislike type is no longer supported. Use 'boost' or 'both'.")
    else:  # both: 왼쪽=정서태그(리뷰 기반), 오른쪽=좋아하는태그
        fig, axes = plt.subplots(1, 2, figsize=(20, 6))
        # 두 패널 사이 간격 조정
        plt.subplots_adjust(wspace=0.25)

        # 왼쪽: 정서태그 - emotion_scores 중 임계값 이상만 (설문 초기값 제외)
        EMOTION_THRESHOLD = 0.25
        review_emotions = {k: v for k, v in emotion_scores.items() if v >= EMOTION_THRESHOLD}

        if review_emotions:
            axes[0].imshow(make_wc_from_freq(review_emotions, "Purples"), interpolation="bilinear")
        else:
            axes[0].text(0.5, 0.5, "리뷰를 더 남겨보세요!", ha="center", va="center",
                         fontsize=13, fontproperties=fp, color="#888888")
        axes[0].axis("off")

        # 오른쪽: 좋아하는 태그 (boost_tags, 파랑 계열)
        if boost_tags:
            axes[1].imshow(make_wc_from_list(boost_tags, "Blues"), interpolation="bilinear")
        else:
            axes[1].text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                         fontsize=14, fontproperties=fp)
        axes[1].axis("off")

    plt.tight_layout(pad=0)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
