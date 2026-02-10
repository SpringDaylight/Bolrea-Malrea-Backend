"""
Authentication API endpoints (Kakao OAuth)
"""
import os
import requests
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from db import get_db
from schemas import UserResponse, MessageResponse
from repositories.user import UserRepository
from models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Kakao OAuth settings
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:5174/auth/kakao/callback")
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


@router.get("/kakao/login")
def kakao_login():
    """Redirect to Kakao OAuth login page"""
    if not KAKAO_CLIENT_ID:
        raise HTTPException(status_code=500, detail="KAKAO_CLIENT_ID is not configured")
    kakao_oauth_url = (
        f"{KAKAO_AUTH_URL}?"
        f"client_id={KAKAO_CLIENT_ID}&"
        f"redirect_uri={KAKAO_REDIRECT_URI}&"
        f"response_type=code"
    )
    return {"auth_url": kakao_oauth_url}


@router.get("/kakao/callback")
def kakao_callback(
    code: str = Query(..., description="Authorization code from Kakao"),
    db: Session = Depends(get_db)
):
    """Handle Kakao OAuth callback"""
    
    # Exchange code for access token
    token_response = requests.post(
        KAKAO_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token from Kakao")
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from Kakao")
    
    # Get user info from Kakao
    user_response = requests.get(
        KAKAO_USER_INFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info from Kakao")
    
    user_data = user_response.json()
    kakao_id = str(user_data.get("id"))
    kakao_account = user_data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    
    # Create user ID with kakao prefix
    user_id = f"kakao_{kakao_id}"
    nickname = profile.get("nickname", f"User{kakao_id[:6]}")
    
    # Check if user exists, create if not
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    
    if not user:
        user = user_repo.create({
            "id": user_id,
            "name": nickname,
            "avatar_text": "카카오 로그인 사용자"
        })
    
    # Return user info (in production, you'd return a JWT token here)
    return {
        "user_id": user.id,
        "name": user.name,
        "avatar_text": user.avatar_text,
        "access_token": access_token  # For demo purposes
    }


@router.post("/logout")
def logout():
    """Logout user"""
    return MessageResponse(message="Logged out successfully")
