"""
LORENZ SaaS - User Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.schemas.auth import UserResponse
from app.api.deps import get_current_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    """
    return current_user


class UserUpdateRequest(BaseModel):
    """Request for updating user profile"""
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None

    class Config:
        extra = "allow"


class PreferencesUpdateRequest(BaseModel):
    """Request for updating user preferences"""
    assistant_name: Optional[str] = None
    assistant_birth_date: Optional[str] = None
    assistant_zodiac: Optional[str] = None
    assistant_ascendant: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        extra = "allow"


@router.patch("/me")
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    """
    if request.name is not None:
        current_user.name = request.name
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url
    if request.preferences is not None:
        current_prefs = current_user.preferences or {}
        current_user.preferences = {**current_prefs, **request.preferences}

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.patch("/me/preferences")
async def update_preferences(
    request: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user preferences (assistant name, theme, language, etc.).
    """
    current_prefs = current_user.preferences or {}

    # Update only provided fields
    updates = request.model_dump(exclude_unset=True, exclude_none=True)
    current_user.preferences = {**current_prefs, **updates}

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {"message": "Preferences updated", "preferences": current_user.preferences}


@router.post("/me/onboarding/complete")
async def complete_user_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark onboarding as complete for the current user.
    """
    current_user.onboarding_completed = True
    current_user.onboarding_step = "complete"

    db.add(current_user)
    await db.commit()

    return {"message": "Onboarding completed", "onboarding_completed": True}


@router.get("/me/connections")
async def get_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all OAuth connections for current user.
    """
    connections = []
    for conn in current_user.oauth_connections:
        connections.append({
            "id": str(conn.id),
            "provider": conn.provider,
            "provider_email": conn.provider_email,
            "is_valid": conn.is_valid,
            "scopes": conn.scopes,
            "created_at": conn.created_at,
        })
    return {"connections": connections}


@router.delete("/me/connections/{provider}")
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect an OAuth provider.
    """
    for conn in current_user.oauth_connections:
        if conn.provider == provider:
            await db.delete(conn)
            await db.commit()
            return {"message": f"Disconnected from {provider}"}

    raise HTTPException(status_code=404, detail=f"No connection found for {provider}")


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user account.
    This also deletes all associated data (emails, conversations, etc.)
    """
    # Check if user is the only owner of their tenant
    if current_user.role == "owner":
        # Count other users in tenant
        from sqlalchemy import select, func
        from app.models import User as UserModel

        count_query = select(func.count()).where(
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.id != current_user.id
        )
        result = await db.execute(count_query)
        other_users = result.scalar()

        if other_users == 0:
            # Also delete tenant
            await db.delete(current_user.tenant)

    await db.delete(current_user)
    await db.commit()

    return {"message": "Account deleted successfully"}
