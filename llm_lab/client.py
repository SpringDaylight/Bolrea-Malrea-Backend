"""
LLM Client - AWS Bedrock 연동
"""
import boto3
import json
import os
from typing import List, Dict, Optional
from llm_lab.debug_utils import print_request_body, print_response_body


class LLMClient:
    """AWS Bedrock Claude 3 클라이언트"""
    
    def __init__(self, model_id: str = None):
        self.region = os.getenv("AWS_REGION", "ap-northeast-2")
        # Use correct model ID
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        
        # AWS 자격 증명 명시적으로 전달
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # [Fix] AKIA 키 사용 시 세션 토큰 제거 (충돌 방지)
        # 영구 IAM 사용자 키(AKIA)와 임시 세션 토큰이 섞이면 인증 오류 발생
        if aws_access_key_id and aws_access_key_id.startswith('AKIA'):
            if 'AWS_SESSION_TOKEN' in os.environ:
                del os.environ['AWS_SESSION_TOKEN']
                print("⚠️ AWS_SESSION_TOKEN 제거됨 (AKIA 키와 충돌 방지)")
        
        if aws_access_key_id and aws_secret_access_key:
            # 명시적 세션 생성으로 전역 세션 오염 방지
            session = boto3.Session(
                region_name=self.region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            self.client = session.client("bedrock-runtime")
        else:
            # 환경변수 없으면 기본 자격 증명 체인 사용
            self.client = boto3.client("bedrock-runtime", region_name=self.region)
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        Generate response from LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with 'response' and 'usage' keys
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        # 디버깅: Request body 출력
        print_request_body(body)

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read())
        
        # 디버깅: Response body 출력
        print_response_body(response_body)
        
        return {
            "response": response_body["content"][0]["text"],
            "usage": {
                "input_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response_body.get("usage", {}).get("output_tokens", 0)
            }
        }
    
    def generate_simple(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Simple text generation
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        result = self.generate(messages, system_prompt=system_prompt)
        return result["response"]
