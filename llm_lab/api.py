"""
LLM Chat API for movie recommendation experimentation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os

router = APIRouter(prefix="/api/llm", tags=["llm-chat"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class ChatResponse(BaseModel):
    response: str
    usage: Optional[dict] = None


def get_bedrock_client():
    """Get AWS Bedrock client"""
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.client("bedrock-runtime", region_name=region)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with LLM for movie recommendation experimentation
    """
    try:
        client = get_bedrock_client()
        
        # Build conversation for Claude
        conversation = []
        for msg in request.messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Prepare request body for Claude 3
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": conversation
        }
        
        # Add system prompt if provided
        if request.system_prompt:
            body["system"] = request.system_prompt
        
        # Call Bedrock - use correct model ID
        model_id = os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        # Parse response
        response_body = json.loads(response["body"].read())
        
        assistant_message = response_body["content"][0]["text"]
        usage = {
            "input_tokens": response_body.get("usage", {}).get("input_tokens", 0),
            "output_tokens": response_body.get("usage", {}).get("output_tokens", 0)
        }
        
        return ChatResponse(
            response=assistant_message,
            usage=usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM chat error: {str(e)}")


@router.get("/system-prompts")
async def get_system_prompts():
    """
    Get predefined system prompts for movie recommendation
    """
    return {
        "prompts": [
            {
                "name": "기본 영화 추천",
                "prompt": "당신은 영화 추천 전문가입니다. 사용자의 감정과 취향을 분석하여 적절한 영화를 추천해주세요."
            },
            {
                "name": "감성 기반 추천",
                "prompt": "당신은 감성 분석 전문가입니다. 사용자가 표현한 감정(우울, 설렘, 긴장 등)을 파악하고, 그 감정에 맞는 영화를 추천해주세요. 추천 시 감정 점수를 JSON 형식으로 제공하세요."
            },
            {
                "name": "서사 구조 분석",
                "prompt": "당신은 영화 서사 분석 전문가입니다. 사용자의 선호하는 서사 구조(반전, 성장, 갈등 등)를 파악하고 적절한 영화를 추천해주세요."
            },
            {
                "name": "자유 대화형",
                "prompt": "당신은 친근한 영화 친구입니다. 자연스럽게 대화하면서 사용자의 취향을 파악하고 영화를 추천해주세요."
            }
        ]
    }
