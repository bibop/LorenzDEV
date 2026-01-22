"""
LORENZ SaaS - User Model
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model - represents an individual user within a tenant.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null if OAuth-only

    # Profile
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Role
    role = Column(String(50), default="member")  # owner, admin, member

    # Telegram integration
    telegram_chat_id = Column(BigInteger, nullable=True, unique=True, index=True)
    telegram_verification_code = Column(String(10), nullable=True)
    telegram_verification_expires = Column(String(50), nullable=True)

    # Preferences
    preferences = Column(JSONB, default=dict)
    # Example preferences:
    # {
    #     "language": "en",
    #     "timezone": "Europe/Rome",
    #     "notifications": {"email": true, "telegram": true},
    #     "ai_model": "claude-3-5-sonnet"
    # }

    # Onboarding status
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(String(50), default="account")

    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    oauth_connections = relationship("OAuthConnection", back_populates="user", cascade="all, delete-orphan")
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    rag_documents = relationship("RAGDocument", back_populates="user", cascade="all, delete-orphan")
    twin_profile = relationship("TwinProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    unified_contacts = relationship("UnifiedContact", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        """Get user's full name or derive from email"""
        return self.name or self.email.split("@")[0].title()

    def __repr__(self):
        return f"<User {self.email}>"
