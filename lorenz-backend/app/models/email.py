"""
LORENZ SaaS - Email Account Model
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class EmailAccount(Base, TimestampMixin):
    """
    Email Account model - stores email account configuration.
    Supports OAuth (Gmail, Outlook) and IMAP credentials.
    """
    __tablename__ = "email_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Email address
    email = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)

    # Provider type
    provider = Column(String(50), nullable=False)  # gmail, outlook, imap

    # OAuth connection (for Gmail/Outlook)
    oauth_connection_id = Column(UUID(as_uuid=True), ForeignKey("oauth_connections.id", ondelete="SET NULL"), nullable=True)

    # IMAP/SMTP credentials (for generic IMAP - encrypted)
    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, default=993)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    password_encrypted = Column(Text, nullable=True)  # Encrypted password for IMAP

    # Email signature
    signature = Column(Text, nullable=True)

    # Settings
    is_primary = Column(Boolean, default=False)
    sync_enabled = Column(Boolean, default=True)
    sync_folders = Column(JSONB, default=lambda: ["INBOX"])  # Folders to sync

    # Sync status
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_uid = Column(String(100), nullable=True)  # Last synced email UID
    sync_status = Column(String(50), default="pending")  # pending, syncing, synced, error
    sync_error = Column(Text, nullable=True)

    # Statistics
    stats = Column(JSONB, default=dict)
    # Example:
    # {
    #     "total_emails": 1000,
    #     "unread_count": 50,
    #     "last_received": "2026-01-15T10:00:00Z"
    # }

    # RAG indexing
    rag_indexed = Column(Boolean, default=False)
    rag_last_indexed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="email_accounts")
    oauth_connection = relationship("OAuthConnection", back_populates="email_accounts")

    def __repr__(self):
        return f"<EmailAccount {self.email}>"
