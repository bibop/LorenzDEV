"""
LORENZ SaaS - Authentication Service
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import logging

from app.config import settings
from app.models import User, Tenant
from app.schemas.auth import UserCreate, UserResponse, TokenResponse

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and user management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def hash_password(self, password: str) -> str:
        """Hash a password (truncate to 72 bytes for bcrypt)"""
        return pwd_context.hash(password[:72])

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash (truncate to 72 bytes for bcrypt)"""
        return pwd_context.verify(plain_password[:72], hashed_password)

    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    async def create_user(self, user_data: UserCreate) -> TokenResponse:
        """Create a new user and tenant"""
        # Check if user exists
        query = select(User).where(User.email == user_data.email)
        result = await self.db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Email already registered")

        # Create tenant
        workspace_name = user_data.workspace_name or f"{user_data.email.split('@')[0]}'s Workspace"
        slug = self._generate_slug(workspace_name)

        tenant = Tenant(
            name=workspace_name,
            slug=slug,
            plan="free"
        )
        self.db.add(tenant)
        await self.db.flush()  # Get tenant ID

        # Create user
        user = User(
            tenant_id=tenant.id,
            email=user_data.email,
            password_hash=self.hash_password(user_data.password),
            name=user_data.name,
            role="owner",
            onboarding_step="email"  # Skip account step
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        access_token = self.create_access_token(str(user.id))
        refresh_token = self.create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        """Authenticate user with email and password"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid email or password")

        if not user.password_hash:
            raise ValueError("This account uses OAuth login")

        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is disabled")

        # Generate tokens
        access_token = self.create_access_token(str(user.id))
        refresh_token = self.create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
        except Exception as e:
            raise ValueError("Invalid refresh token")

        # Get user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Generate new tokens
        new_access_token = self.create_access_token(str(user.id))
        new_refresh_token = self.create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    async def generate_telegram_verification(self, user: User) -> str:
        """Generate a verification code for Telegram linking"""
        code = secrets.token_hex(3).upper()  # 6 character code
        user.telegram_verification_code = code
        user.telegram_verification_expires = (
            datetime.utcnow() + timedelta(minutes=10)
        ).isoformat()

        self.db.add(user)
        await self.db.commit()

        return code

    async def verify_telegram_code(self, user: User, code: str) -> bool:
        """Verify Telegram code (called from web)"""
        if not user.telegram_verification_code:
            raise ValueError("No verification pending")

        if user.telegram_verification_code != code:
            raise ValueError("Invalid verification code")

        # Check expiry
        if user.telegram_verification_expires:
            expires = datetime.fromisoformat(user.telegram_verification_expires)
            if datetime.utcnow() > expires:
                raise ValueError("Verification code expired")

        # Code is valid - clear it
        user.telegram_verification_code = None
        user.telegram_verification_expires = None
        self.db.add(user)
        await self.db.commit()

        return True

    def _generate_slug(self, name: str) -> str:
        """Generate a unique slug from name"""
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug[:50]  # Limit length
        return f"{slug}-{secrets.token_hex(3)}"
