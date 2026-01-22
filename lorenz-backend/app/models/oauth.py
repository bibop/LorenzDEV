"""
LORENZ SaaS - OAuth Connection Model
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class OAuthConnection(Base, TimestampMixin):
    """
    OAuth Connection model - stores OAuth tokens for various providers.
    Tokens are encrypted at rest.
    """
    __tablename__ = "oauth_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Provider info
    provider = Column(String(50), nullable=False, index=True)
    # Providers: google, microsoft, linkedin, twitter, meta, dropbox

    provider_user_id = Column(String(255), nullable=True)  # User ID from the provider
    provider_email = Column(String(255), nullable=True)  # Email from the provider

    # Tokens (encrypted)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Scopes granted
    scopes = Column(ARRAY(String), default=list)

    # Additional metadata from provider
    provider_metadata = Column(JSONB, default=dict)
    # Example:
    # {
    #     "profile_url": "...",
    #     "profile_picture": "...",
    #     "account_type": "personal/business"
    # }

    # Status
    is_valid = Column(String(20), default="valid")  # valid, expired, revoked

    # Relationships
    user = relationship("User", back_populates="oauth_connections")
    email_accounts = relationship("EmailAccount", back_populates="oauth_connection")
    social_accounts = relationship("SocialAccount", back_populates="oauth_connection")

    def __repr__(self):
        return f"<OAuthConnection {self.provider} for user {self.user_id}>"

    class Config:
        # Unique constraint on user_id + provider
        __table_args__ = (
            {"extend_existing": True},
        )
