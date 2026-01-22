"""
LORENZ SaaS - Chat Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None  # None = new conversation
    channel: str = Field(default="web", pattern="^(web|telegram|mobile|api)$")
    context: Optional[dict] = None  # Additional context
    attachments: Optional[List[dict]] = []  # [{type, data}]


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    message_type: str
    attachments: List[dict]
    model: Optional[str]
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: UUID
    title: Optional[str]
    channel: str
    model: str
    total_tokens: int
    is_active: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    last_message: Optional[ChatMessageResponse] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for conversation list"""
    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class ChatStreamChunk(BaseModel):
    """Schema for streaming chat response"""
    type: str  # "text", "tool_call", "tool_result", "done", "error"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_result: Optional[dict] = None
    error: Optional[str] = None


class AIContextRequest(BaseModel):
    """Schema for getting AI context"""
    query: str
    include_emails: bool = True
    include_calendar: bool = True
    include_rag: bool = True
    max_context_items: int = Field(default=10, le=50)
