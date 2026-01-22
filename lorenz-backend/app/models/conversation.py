"""
LORENZ SaaS - Conversation and Message Models
"""

from sqlalchemy import Column, String, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    """
    Conversation model - represents a chat session with LORENZ.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Channel
    channel = Column(String(50), nullable=False, default="web")
    # Channels: web, telegram, mobile, api

    # Title (auto-generated or user-set)
    title = Column(String(255), nullable=True)

    # Context for AI
    context = Column(JSONB, default=dict)
    # Example:
    # {
    #     "topic": "email management",
    #     "entities": ["John Doe", "Project X"],
    #     "preferences": {"tone": "professional"}
    # }

    # AI model used
    model = Column(String(100), default="claude-3-5-sonnet")

    # Token usage
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Integer, default=0)  # Stored as cents

    # Status
    is_active = Column(String(20), default="active")  # active, archived

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation {self.id}>"


class Message(Base, TimestampMixin):
    """
    Message model - individual messages within a conversation.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Role
    role = Column(String(20), nullable=False)  # user, assistant, system

    # Content
    content = Column(Text, nullable=False)

    # Message type
    message_type = Column(String(50), default="text")
    # Types: text, email_summary, calendar_event, social_post, file_analysis, etc.

    # Attachments/References
    attachments = Column(JSONB, default=list)
    # Example:
    # [
    #     {"type": "email", "id": "...", "subject": "..."},
    #     {"type": "file", "url": "...", "name": "..."}
    # ]

    # AI metadata
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Integer, default=0)  # Stored as cents * 1000

    # Tool calls (for function calling)
    tool_calls = Column(JSONB, default=list)
    tool_results = Column(JSONB, default=list)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.role}: {self.content[:50]}...>"
