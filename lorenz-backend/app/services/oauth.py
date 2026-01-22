"""
LORENZ SaaS - OAuth Service
Handles OAuth flows for Google, Microsoft, LinkedIn, Twitter, Meta
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlencode
import secrets
import aiohttp
import logging

from app.config import settings
from app.models import User, Tenant, OAuthConnection
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

# OAuth state storage (in production, use Redis)
_oauth_states: Dict[str, Dict[str, Any]] = {}


class OAuthService:
    """OAuth authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_authorization_url(
        self,
        provider: str,
        user_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Get OAuth authorization URL for a provider.
        Returns (authorization_url, state)
        """
        state = secrets.token_urlsafe(32)

        # Store state with user_id if linking to existing account
        _oauth_states[state] = {
            "user_id": user_id,
            "provider": provider
        }

        if provider == "google":
            return self._get_google_auth_url(state), state
        elif provider == "microsoft":
            return self._get_microsoft_auth_url(state), state
        elif provider == "linkedin":
            return self._get_linkedin_auth_url(state), state
        elif provider == "twitter":
            return self._get_twitter_auth_url(state), state
        elif provider == "meta":
            return self._get_meta_auth_url(state), state
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def handle_callback(
        self,
        provider: str,
        code: str,
        state: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback.
        Returns either tokens (for new user) or redirect info (for linking).
        """
        # Validate state
        if state and state in _oauth_states:
            state_data = _oauth_states.pop(state)
            user_id = state_data.get("user_id")
        else:
            user_id = None

        # Exchange code for tokens
        if provider == "google":
            token_data = await self._exchange_google_code(code)
            user_info = await self._get_google_user_info(token_data["access_token"])
        elif provider == "microsoft":
            token_data = await self._exchange_microsoft_code(code)
            user_info = await self._get_microsoft_user_info(token_data["access_token"])
        elif provider == "linkedin":
            token_data = await self._exchange_linkedin_code(code)
            user_info = await self._get_linkedin_user_info(token_data["access_token"])
        elif provider == "twitter":
            token_data = await self._exchange_twitter_code(code)
            user_info = await self._get_twitter_user_info(token_data["access_token"])
        elif provider == "meta":
            token_data = await self._exchange_meta_code(code)
            user_info = await self._get_meta_user_info(token_data["access_token"])
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # If user_id provided, link to existing account
        if user_id:
            await self._link_oauth_account(
                user_id=user_id,
                provider=provider,
                token_data=token_data,
                user_info=user_info
            )
            return {
                "redirect_url": f"{settings.FRONTEND_URL}/settings/connections"
            }

        # Otherwise, find or create user
        user = await self._find_or_create_user(provider, token_data, user_info)

        # Generate tokens
        auth_service = AuthService(self.db)
        access_token = auth_service.create_access_token(str(user.id))
        refresh_token = auth_service.create_refresh_token(str(user.id))

        from app.schemas.auth import UserResponse, TokenResponse
        return {
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user)
            )
        }

    async def _link_oauth_account(
        self,
        user_id: str,
        provider: str,
        token_data: dict,
        user_info: dict
    ):
        """Link OAuth account to existing user"""
        # Check if connection already exists
        query = select(OAuthConnection).where(
            OAuthConnection.user_id == user_id,
            OAuthConnection.provider == provider
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing connection
            existing.access_token = token_data.get("access_token")
            existing.refresh_token = token_data.get("refresh_token")
            existing.token_expires_at = token_data.get("expires_at")
            existing.is_valid = "valid"
            self.db.add(existing)
        else:
            # Create new connection
            connection = OAuthConnection(
                user_id=user_id,
                provider=provider,
                provider_user_id=user_info.get("id"),
                provider_email=user_info.get("email"),
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                token_expires_at=token_data.get("expires_at"),
                scopes=token_data.get("scope", "").split(),
                metadata=user_info
            )
            self.db.add(connection)

        await self.db.commit()

    async def _find_or_create_user(
        self,
        provider: str,
        token_data: dict,
        user_info: dict
    ) -> User:
        """Find existing user by OAuth or create new one"""
        email = user_info.get("email")
        provider_user_id = user_info.get("id")

        # First, try to find by OAuth connection
        query = select(OAuthConnection).where(
            OAuthConnection.provider == provider,
            OAuthConnection.provider_user_id == provider_user_id
        )
        result = await self.db.execute(query)
        connection = result.scalar_one_or_none()

        if connection:
            # Update tokens
            connection.access_token = token_data.get("access_token")
            connection.refresh_token = token_data.get("refresh_token")
            connection.is_valid = "valid"
            self.db.add(connection)
            await self.db.commit()

            # Get user
            query = select(User).where(User.id == connection.user_id)
            result = await self.db.execute(query)
            return result.scalar_one()

        # Try to find by email
        if email:
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                # Link OAuth to existing user
                await self._link_oauth_account(
                    user_id=str(user.id),
                    provider=provider,
                    token_data=token_data,
                    user_info=user_info
                )
                return user

        # Create new user and tenant
        name = user_info.get("name") or email.split("@")[0]
        workspace_name = f"{name}'s Workspace"

        tenant = Tenant(
            name=workspace_name,
            slug=f"{name.lower().replace(' ', '-')}-{secrets.token_hex(3)}",
            plan="free"
        )
        self.db.add(tenant)
        await self.db.flush()

        user = User(
            tenant_id=tenant.id,
            email=email,
            name=name,
            avatar_url=user_info.get("picture"),
            role="owner",
            email_verified=True,  # OAuth emails are verified
            onboarding_step="email"
        )
        self.db.add(user)
        await self.db.flush()

        # Create OAuth connection
        connection = OAuthConnection(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=token_data.get("expires_at"),
            scopes=token_data.get("scope", "").split(),
            metadata=user_info
        )
        self.db.add(connection)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    # Google OAuth
    def _get_google_auth_url(self, state: str) -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def _exchange_google_code(self, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI
                }
            ) as resp:
                return await resp.json()

    async def _get_google_user_info(self, access_token: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as resp:
                return await resp.json()

    # Microsoft OAuth
    def _get_microsoft_auth_url(self, state: str) -> str:
        params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile offline_access Mail.Read Mail.Send Calendars.ReadWrite",
            "state": state,
            "response_mode": "query"
        }
        return f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(params)}"

    async def _exchange_microsoft_code(self, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.MICROSOFT_REDIRECT_URI
                }
            ) as resp:
                return await resp.json()

    async def _get_microsoft_user_info(self, access_token: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as resp:
                data = await resp.json()
                return {
                    "id": data.get("id"),
                    "email": data.get("mail") or data.get("userPrincipalName"),
                    "name": data.get("displayName"),
                    "picture": None  # MS Graph requires separate call for photo
                }

    # LinkedIn OAuth
    def _get_linkedin_auth_url(self, state: str) -> str:
        params = {
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email w_member_social",
            "state": state
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    async def _exchange_linkedin_code(self, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "client_id": settings.LINKEDIN_CLIENT_ID,
                    "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.LINKEDIN_REDIRECT_URI
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as resp:
                return await resp.json()

    async def _get_linkedin_user_info(self, access_token: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as resp:
                return await resp.json()

    # Twitter/X OAuth (placeholder - X API v2)
    def _get_twitter_auth_url(self, state: str) -> str:
        # Twitter OAuth 2.0 with PKCE
        params = {
            "client_id": settings.TWITTER_CLIENT_ID,
            "redirect_uri": settings.TWITTER_REDIRECT_URI,
            "response_type": "code",
            "scope": "tweet.read tweet.write users.read offline.access",
            "state": state,
            "code_challenge": "challenge",  # In production, generate proper PKCE
            "code_challenge_method": "plain"
        }
        return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"

    async def _exchange_twitter_code(self, code: str) -> dict:
        # Placeholder
        return {}

    async def _get_twitter_user_info(self, access_token: str) -> dict:
        # Placeholder
        return {}

    # Meta (Facebook/Instagram) OAuth
    def _get_meta_auth_url(self, state: str) -> str:
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_REDIRECT_URI,
            "response_type": "code",
            "scope": "email,public_profile,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish",
            "state": state
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"

    async def _exchange_meta_code(self, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "code": code,
                    "redirect_uri": settings.META_REDIRECT_URI
                }
            ) as resp:
                return await resp.json()

    async def _get_meta_user_info(self, access_token: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.facebook.com/me",
                params={
                    "fields": "id,name,email,picture",
                    "access_token": access_token
                }
            ) as resp:
                return await resp.json()
