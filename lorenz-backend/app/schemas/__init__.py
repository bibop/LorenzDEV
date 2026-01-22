"""
LORENZ SaaS - Pydantic Schemas
Request/Response models for API validation
"""

from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    OAuthCallbackRequest,
)
from app.schemas.email import (
    EmailAccountCreate,
    EmailAccountResponse,
    EmailMessageResponse,
    EmailSendRequest,
)
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "OAuthCallbackRequest",
    "EmailAccountCreate",
    "EmailAccountResponse",
    "EmailMessageResponse",
    "EmailSendRequest",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ConversationResponse",
]
