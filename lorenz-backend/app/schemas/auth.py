"""
LORENZ SaaS - Authentication Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    workspace_name: Optional[str] = None  # Creates a new tenant if provided


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    tenant_id: UUID
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str
    telegram_chat_id: Optional[int]
    onboarding_completed: bool
    onboarding_step: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback"""
    code: str
    state: Optional[str] = None


class OAuthStartResponse(BaseModel):
    """Schema for OAuth start response"""
    authorization_url: str
    state: str


class TelegramVerificationRequest(BaseModel):
    """Schema for Telegram verification"""
    verification_code: str


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh"""
    refresh_token: str
