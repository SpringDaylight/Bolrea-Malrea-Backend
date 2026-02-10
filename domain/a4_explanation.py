# 설명 생성 로직
def explain_prediction(payload: dict) -> dict:
    """
    A-4: 설명 가능한 추천
    """
    movie_title = payload.get("movie_title", "Unknown")
    match_rate = payload.get("match_rate", 73.0)

    return {
        "movie_title": movie_title,
        "match_rate": match_rate,
        "explanation": (
            f"'{movie_title}' is recommended based on matching emotional tone "
            "and narrative preferences."
        ),
        "key_factors": [
            {"category": "emotion", "tag": "warm", "score": 0.8},
            {"category": "story_flow", "tag": "growth", "score": 0.6},
        ],
        "disclaimer": "Recommendation is based on tag-level analysis and may vary by user.",
    }
