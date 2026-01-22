"""
LORENZ SaaS - Email Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EmailAccountCreate(BaseModel):
    """Schema for creating an email account"""
    email: EmailStr
    display_name: Optional[str] = None
    provider: str = Field(..., pattern="^(gmail|outlook|imap)$")

    # IMAP credentials (only for provider="imap")
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    password: Optional[str] = None

    # Signature
    signature: Optional[str] = None


class EmailAccountUpdate(BaseModel):
    """Schema for updating an email account"""
    display_name: Optional[str] = None
    signature: Optional[str] = None
    is_primary: Optional[bool] = None
    sync_enabled: Optional[bool] = None
    sync_folders: Optional[List[str]] = None


class EmailAccountResponse(BaseModel):
    """Schema for email account response"""
    id: UUID
    email: str
    display_name: Optional[str]
    provider: str
    is_primary: bool
    sync_enabled: bool
    sync_status: str
    last_sync_at: Optional[datetime]
    stats: dict
    created_at: datetime

    class Config:
        from_attributes = True


class EmailMessageResponse(BaseModel):
    """Schema for email message response"""
    id: str  # Message UID
    account_id: UUID
    subject: Optional[str]
    from_address: str
    from_name: Optional[str]
    to_addresses: List[str]
    cc_addresses: Optional[List[str]] = []
    date: datetime
    snippet: Optional[str]  # Preview text
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    is_read: bool
    is_starred: bool
    has_attachments: bool
    attachments: Optional[List[dict]] = []
    labels: Optional[List[str]] = []
    thread_id: Optional[str] = None


class EmailSendRequest(BaseModel):
    """Schema for sending an email"""
    account_id: UUID
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    subject: str
    body: str  # HTML body
    body_text: Optional[str] = None  # Plain text alternative
    reply_to_message_id: Optional[str] = None  # For replies
    attachments: Optional[List[dict]] = []  # [{name, content_base64, mime_type}]


class EmailSendResponse(BaseModel):
    """Schema for email send response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailSearchRequest(BaseModel):
    """Schema for email search"""
    account_id: Optional[UUID] = None  # None = search all accounts
    query: str
    folder: Optional[str] = "INBOX"
    limit: int = Field(default=50, le=100)
    offset: int = 0


class EmailStatsResponse(BaseModel):
    """Schema for email statistics"""
    total_accounts: int
    total_emails: int
    unread_count: int
    today_received: int
    accounts: List[dict]
