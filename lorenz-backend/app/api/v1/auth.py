"""
LORENZ SaaS - Authentication Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import secrets
import logging

from app.database import get_db
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    OAuthCallbackRequest,
    OAuthStartResponse,
    RefreshTokenRequest,
    TelegramVerificationRequest,
)
from app.services.auth import AuthService
from app.services.oauth import OAuthService
from app.api.deps import get_current_user, get_current_user_optional
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user and create a tenant/workspace.
    """
    auth_service = AuthService(db)
    try:
        token_response = await auth_service.create_user(user_data)
        return token_response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with email and password.
    """
    auth_service = AuthService(db)
    try:
        token_response = await auth_service.authenticate(
            credentials.email,
            credentials.password
        )
        return token_response
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    try:
        token_response = await auth_service.refresh_tokens(request.refresh_token)
        return token_response
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user (invalidate tokens).
    """
    # In a production app, you'd add the token to a blacklist in Redis
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user.
    """
    return current_user


# OAuth Routes

@router.get("/oauth/{provider}", response_model=OAuthStartResponse)
async def oauth_start(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Start OAuth flow for a provider.
    Provider can be: google, microsoft, linkedin, twitter, meta
    """
    oauth_service = OAuthService(db)
    try:
        auth_url, state = await oauth_service.get_authorization_url(
            provider,
            user_id=str(current_user.id) if current_user else None
        )
        return OAuthStartResponse(authorization_url=auth_url, state=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from provider.
    Either creates a new user or links to existing user.
    """
    oauth_service = OAuthService(db)
    try:
        result = await oauth_service.handle_callback(provider, code, state)

        # If it's a new user login, return tokens
        if "tokens" in result:
            return result["tokens"]

        # If it's linking to existing account, redirect to frontend
        return RedirectResponse(
            url=f"{result['redirect_url']}?success=true&provider={provider}"
        )
    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Telegram Verification

@router.post("/telegram/start-verification")
async def start_telegram_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a verification code for linking Telegram account.
    User should send this code to the LORENZ bot.
    """
    auth_service = AuthService(db)
    code = await auth_service.generate_telegram_verification(current_user)
    return {
        "verification_code": code,
        "bot_username": "lorenz_bot",
        "instructions": "Send this code to @lorenz_bot on Telegram to link your account"
    }


@router.post("/telegram/verify")
async def verify_telegram(
    request: TelegramVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify Telegram account with the code sent to the bot.
    This is called by the web frontend after user sends code to bot.
    """
    auth_service = AuthService(db)
    try:
        success = await auth_service.verify_telegram_code(
            current_user,
            request.verification_code
        )
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
