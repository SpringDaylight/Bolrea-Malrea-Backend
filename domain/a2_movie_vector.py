from domain.taxonomy import load_taxonomy
from domain.a1_preference import _stable_score


def _movie_text(movie_payload: dict) -> str:
    parts = []
    for key in ["title", "overview"]:
        val = movie_payload.get(key)
        if val:
            parts.append(str(val))
    for key in ["keywords", "genres", "directors", "cast"]:
        val = movie_payload.get(key)
        if isinstance(val, list):
            parts.extend([str(v) for v in val])
    return " ".join(parts)


def _top_tags(scores: dict, top_n: int = 3) -> list[str]:
    return [k for k, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]]


def process_movie_vector(movie_payload: dict) -> dict:
    """
    A-2: 영화 입력 -> 영화 프로필 (taste-simulation-engine 형식 맞춤)
    """
    movie_id = movie_payload.get("movie_id", "dummy_movie")
    title = movie_payload.get("title", "Dummy Movie")
    text = _movie_text(movie_payload)

    taxonomy = load_taxonomy()
    e_keys = taxonomy.get("emotion", {}).get("tags", [])
    n_keys = taxonomy.get("story_flow", {}).get("tags", [])
    d_keys = taxonomy.get("direction_mood", {}).get("tags", [])
    c_keys = taxonomy.get("character_relationship", {}).get("tags", [])

    emotion_scores = {k: _stable_score(text, k) for k in e_keys}
    narrative_traits = {k: _stable_score(text, k) for k in n_keys}
    direction_mood = {k: _stable_score(text, k) for k in d_keys}
    character_relationship = {k: _stable_score(text, k) for k in c_keys}

    profile = {
        "movie_id": movie_id,
        "title": title,
        "emotion_scores": emotion_scores,
        "narrative_traits": narrative_traits,
        "direction_mood": direction_mood,
        "character_relationship": character_relationship,
        "ending_preference": {
            "happy": _stable_score(text, "ending_happy"),
            "open": _stable_score(text, "ending_open"),
            "bittersweet": _stable_score(text, "ending_bittersweet"),
        },
    }

    top_emotions = ", ".join(_top_tags(emotion_scores))
    top_narrative = ", ".join(_top_tags(narrative_traits))
    profile["embedding_text"] = f"Title: {title}. Emotions: {top_emotions}. Narrative: {top_narrative}."
    profile["embedding"] = []
    return profile
