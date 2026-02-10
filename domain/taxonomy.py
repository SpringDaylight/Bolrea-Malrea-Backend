import json
from pathlib import Path


def _default_taxonomy() -> dict:
    return {
        "emotion": {"tags": ["감동적이에요", "잔잔해요"]},
        "story_flow": {"tags": ["성장", "관계"]},
        "direction_mood": {"tags": ["밝은 분위기예요", "어두운 분위기예요"]},
        "character_relationship": {"tags": ["관계 중심", "주인공 중심"]},
    }


def load_taxonomy() -> dict:
    base = Path(__file__).resolve().parents[3]
    path = base / "taste-simulation-engine" / "model_sample" / "emotion_tag.json"
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _default_taxonomy()
