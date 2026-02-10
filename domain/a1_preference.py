from domain.taxonomy import load_taxonomy


def _stable_score(text: str, tag: str) -> float:
    seed = (text + "||" + tag).encode("utf-8")
    h = 0
    for b in seed:
        h = (h * 131 + b) % 1000003
    return round((h % 1000) / 1000.0, 3)


def analyze_preference(payload: dict) -> dict:
    """
    A-1: 사용자 텍스트 -> 취향 벡터
    """
    text = payload.get("text", "")
    dislikes_text = payload.get("dislikes", "")
    dislike_tags = []
    if isinstance(dislikes_text, str) and dislikes_text.strip():
        dislike_tags = [t.strip() for t in dislikes_text.split(",") if t.strip()]

    taxonomy = load_taxonomy()
    e_keys = taxonomy.get("emotion", {}).get("tags", [])
    n_keys = taxonomy.get("story_flow", {}).get("tags", [])

    emotion_scores = {k: _stable_score(text, k) for k in e_keys}
    narrative_traits = {k: _stable_score(text, k) for k in n_keys}

    ending_preference = {
        "happy": _stable_score(text, "ending_happy"),
        "open": _stable_score(text, "ending_open"),
        "bittersweet": _stable_score(text, "ending_bittersweet"),
    }

    return {
        "user_text": text,
        "emotion_scores": emotion_scores,
        "narrative_traits": narrative_traits,
        "ending_preference": ending_preference,
        "dislike_tags": dislike_tags,
    }
