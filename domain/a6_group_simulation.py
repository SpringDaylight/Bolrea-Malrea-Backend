# 그룹 취향 시뮬레이션
def simulate_group(payload: dict) -> dict:
    """
    A-6: 그룹 사용자 + 영화 프로필로 그룹 만족 확률 계산
    """
    from domain.a3_prediction import calculate_satisfaction_probability

    members = payload.get("members", [])
    movie_profile = payload.get("movie_profile", {})
    penalty_weight = float(payload.get("penalty_weight", 0.7))
    boost_weight = float(payload.get("boost_weight", 0.5))

    if not members:
        return {"group_score": 0.0, "members": [], "comment": "그룹 입력이 없습니다."}

    user_probs = []
    member_results = []

    for m in members:
        profile = m.get("profile", {})
        dislikes = m.get("dislikes", [])
        likes = m.get("likes", [])
        result = calculate_satisfaction_probability(
            user_profile=profile,
            movie_profile=movie_profile,
            dislikes=dislikes,
            boost_tags=likes,
            penalty_weight=penalty_weight,
            boost_weight=boost_weight,
        )
        prob = float(result["probability"])
        user_probs.append(prob)
        member_results.append(
            {
                "user_id": m.get("user_id", ""),
                "probability": result["probability"],
                "confidence": result["confidence"],
                "level": _level_from_prob(prob),
            }
        )

    group_prob = sum(user_probs) / len(user_probs)

    return {
        "group_score": round(group_prob, 3),
        "members": member_results,
        "comment": _group_comment(group_prob),
    }


def _level_from_prob(prob: float) -> str:
    if prob >= 0.85:
        return "매우 만족"
    if prob >= 0.70:
        return "만족"
    if prob >= 0.50:
        return "보통"
    if prob >= 0.30:
        return "불만"
    return "매우 불만"


def _group_comment(prob: float) -> str:
    if prob >= 0.70:
        return "전반적으로 만족도가 높습니다."
    if prob >= 0.50:
        return "의견이 갈릴 수 있습니다."
    return "만족도가 낮을 수 있습니다."
