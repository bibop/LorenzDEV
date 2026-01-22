"""
LORENZ SaaS - Social Account Model
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class SocialAccount(Base, TimestampMixin):
    """
    Social Account model - stores social media account connections.
    """
    __tablename__ = "social_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Platform
    platform = Column(String(50), nullable=False, index=True)
    # Platforms: linkedin, twitter, instagram, facebook

    # OAuth connection
    oauth_connection_id = Column(UUID(as_uuid=True), ForeignKey("oauth_connections.id", ondelete="SET NULL"), nullable=True)

    # Account info from platform
    platform_user_id = Column(String(255), nullable=True)
    platform_username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    profile_url = Column(String(500), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)

    # Account type (personal vs business/page)
    account_type = Column(String(50), default="personal")  # personal, business, page

    # For Facebook/Instagram pages
    page_id = Column(String(255), nullable=True)
    page_name = Column(String(255), nullable=True)
    page_access_token = Column(String(500), nullable=True)  # Encrypted

    # Profile data from API
    profile_data = Column(JSONB, default=dict)

    # Capabilities
    can_read = Column(Boolean, default=True)
    can_post = Column(Boolean, default=True)
    can_dm = Column(Boolean, default=False)

    # Settings
    posting_enabled = Column(Boolean, default=True)
    auto_share_enabled = Column(Boolean, default=False)

    # Sync status
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(50), default="pending")

    # RAG indexing
    rag_indexed = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="social_accounts")
    oauth_connection = relationship("OAuthConnection", back_populates="social_accounts")

    def __repr__(self):
        return f"<SocialAccount {self.platform}:{self.platform_username}>"
