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
from schemas import UserResponse, MessageResponse, UserSignupRequest, UserLoginRequest
from repositories.user import UserRepository
from repositories.user_auth import UserAuthRepository
from models import User
from utils.security import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_user_pk,
)

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
    
    provider = "kakao"
    provider_user_id = kakao_id
    nickname = profile.get("nickname", f"User{kakao_id[:6]}")
    
    # Check if user exists, create if not
    user_repo = UserRepository(db)
    auth_repo = UserAuthRepository(db)

    auth = auth_repo.get_by_provider(provider, provider_user_id)
    if auth:
        user = user_repo.get(auth.user_id)
    else:
        user = user_repo.create({
            "id": generate_user_pk(),
            "name": nickname,
            "nickname": nickname,
            "avatar_text": "카카오 로그인 사용자"
        })
        auth_repo.create({
            "user_id": user.id,
            "provider": provider,
            "provider_user_id": provider_user_id,
            "email": kakao_account.get("email")
        })
    
    # Return user info (in production, you'd return a JWT token here)
    return {
        "user_id": user.user_id,
        "name": user.name,
        "nickname": user.nickname,
        "email": user.email,
        "avatar_text": user.avatar_text,
        "access_token": access_token  # For demo purposes
    }


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(payload: UserSignupRequest, db: Session = Depends(get_db)):
    """Create a local user account"""
    user_repo = UserRepository(db)

    if payload.password != payload.password_confirm:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")

    if not validate_password_policy(payload.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be 8-20 chars and include at least 2 of: uppercase, lowercase, number, special"
        )

    if user_repo.get_by_user_id(payload.user_id):
        raise HTTPException(status_code=400, detail="User ID already exists")
    if user_repo.get_by_nickname(payload.nickname):
        raise HTTPException(status_code=400, detail="Nickname already exists")
    if user_repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    db_user = user_repo.create(
        {
            "id": generate_user_pk(),
            "user_id": payload.user_id,
            "name": payload.name,
            "nickname": payload.nickname,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
        }
    )

    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        user_id=db_user.user_id,
        nickname=db_user.nickname,
        email=db_user.email,
        avatar_text=db_user.avatar_text,
        created_at=db_user.created_at,
    )


@router.post("/login", response_model=UserResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Login with user_id and password"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_user_id(payload.user_id)

    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return UserResponse(
        id=user.id,
        name=user.name,
        user_id=user.user_id,
        nickname=user.nickname,
        email=user.email,
        avatar_text=user.avatar_text,
        created_at=user.created_at,
    )


@router.post("/logout")
def logout():
    """Logout user"""
    return MessageResponse(message="Logged out successfully")
