"""
프롬프트 + 스키마 기반 LLM 실행기

- YAML 프롬프트 로드
- JSON 스키마로 결과 형태 검증
- 실제 LLM/Mock 클라이언트 모두 지원
"""

import json
from pathlib import Path

from llm_client import MockLLMClient


def load_yaml(path: str) -> dict:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "PyYAML이 필요합니다. `pip install pyyaml` 후 다시 실행해주세요."
        ) from exc

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_prompt(prompt_data: dict, input_text: str) -> str:
    # system/user 템플릿에 입력 텍스트 삽입
    system = prompt_data.get("system", "").strip()
    user = prompt_data.get("user", "").strip()
    user = user.replace("{{input_text}}", input_text)
    return f"{system}\n\n{user}".strip()


def validate_schema_basic(schema: dict, data: dict) -> None:
    # 최소 필수 키와 타입만 확인하는 경량 검증
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise ValueError(f"LLM 결과에 필수 키가 없습니다: {key}")

    properties = schema.get("properties", {})
    for key, spec in properties.items():
        if key not in data:
            continue
        expected_type = spec.get("type")
        if expected_type == "array" and not isinstance(data[key], list):
            raise ValueError(f"키 '{key}'는 배열이어야 합니다.")
        if expected_type == "string" and not isinstance(data[key], str):
            raise ValueError(f"키 '{key}'는 문자열이어야 합니다.")


def run(prompt_path: str, schema_path: str, input_text: str, client=None) -> dict:
    prompt_data = load_yaml(prompt_path)
    schema_data = load_json(schema_path)
    prompt_text = render_prompt(prompt_data, input_text)

    if client is None:
        client = MockLLMClient()

    response_text = client.invoke(prompt_text)
    parsed = json.loads(response_text)
    validate_schema_basic(schema_data, parsed)
    return parsed


if __name__ == "__main__":
    base = Path(__file__).parent
    result = run(
        prompt_path=str(base / "prompt" / "a1_user_preference.yaml"),
        schema_path=str(base / "schema" / "user_preference.json"),
        input_text="잔잔했는데 여운이 컸어요",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
