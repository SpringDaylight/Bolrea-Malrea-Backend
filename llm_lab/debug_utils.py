"""
LLM 디버깅 유틸리티
"""
import json
from typing import Dict, Any


def print_request_body(body: Dict[str, Any]) -> None:
    """
    Request body를 보기 좋게 출력
    
    Args:
        body: Request body 딕셔너리
    """
    print("\n" + "="*80)
    print("📤 REQUEST BODY")
    print("="*80)
    
    # JSON을 예쁘게 포맷팅
    formatted = json.dumps(body, indent=2, ensure_ascii=False)
    
    # \n을 실제 개행으로 변환
    formatted = formatted.replace('\\n', '\n')
    
    print(formatted)
    print("="*80 + "\n")


def print_response_body(body: Dict[str, Any]) -> None:
    """
    Response body를 보기 좋게 출력
    
    Args:
        body: Response body 딕셔너리
    """
    print("\n" + "="*80)
    print("📥 RESPONSE BODY")
    print("="*80)
    
    # 주요 정보만 추출
    response_text = ""
    usage_info = {}
    
    if "content" in body and len(body["content"]) > 0:
        response_text = body["content"][0].get("text", "")
    
    if "usage" in body:
        usage_info = body["usage"]
    
    # 응답 텍스트 출력
    print("\n📝 Response Text:")
    print("-" * 80)
    # \n을 실제 개행으로 변환
    print(response_text.replace('\\n', '\n'))
    print("-" * 80)
    
    # 토큰 사용량 출력
    if usage_info:
        print("\n📊 Token Usage:")
        print(f"  Input Tokens:  {usage_info.get('input_tokens', 0):,}")
        print(f"  Output Tokens: {usage_info.get('output_tokens', 0):,}")
        print(f"  Total Tokens:  {usage_info.get('input_tokens', 0) + usage_info.get('output_tokens', 0):,}")
    
    # 메타데이터 출력
    print("\n🔍 Metadata:")
    print(f"  Model: {body.get('model', 'N/A')}")
    print(f"  Stop Reason: {body.get('stop_reason', 'N/A')}")
    
    print("="*80 + "\n")


def print_compact_request(body: Dict[str, Any]) -> None:
    """
    Request body를 간단하게 출력 (한 줄 요약)
    
    Args:
        body: Request body 딕셔너리
    """
    messages = body.get("messages", [])
    message_count = len(messages)
    
    # 첫 메시지 미리보기
    preview = ""
    if messages:
        first_content = messages[0].get("content", "")
        preview = first_content[:50] + "..." if len(first_content) > 50 else first_content
    
    print(f"📤 REQUEST: {message_count} message(s) | Preview: {preview}")


def print_compact_response(body: Dict[str, Any]) -> None:
    """
    Response body를 간단하게 출력 (한 줄 요약)
    
    Args:
        body: Response body 딕셔너리
    """
    response_text = ""
    if "content" in body and len(body["content"]) > 0:
        response_text = body["content"][0].get("text", "")
    
    preview = response_text[:50] + "..." if len(response_text) > 50 else response_text
    
    usage = body.get("usage", {})
    tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    
    print(f"📥 RESPONSE: {tokens:,} tokens | Preview: {preview}")


def print_debug_separator(title: str = "") -> None:
    """
    디버그 구분선 출력
    
    Args:
        title: 구분선 제목
    """
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}\n")
