"""
로컬 프롬프트 테스트 실행기

- a1_user_preference 프롬프트 + 스키마로 샘플 입력 테스트
"""

import json
from pathlib import Path

from llm_executor import run


def main() -> None:
    base = Path(__file__).parent
    result = run(
        prompt_path=str(base / "prompt" / "a1_user_preference.yaml"),
        schema_path=str(base / "schema" / "user_preference.json"),
        input_text="잔잔했는데 보고 나서 계속 생각이 났어요",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
