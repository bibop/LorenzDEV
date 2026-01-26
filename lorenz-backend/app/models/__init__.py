"""
LORENZ SaaS - SQLAlchemy Models
Multi-tenant database models with Row-Level Security support
"""

from app.models.base import Base, TimestampMixin, TenantMixin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.oauth import OAuthConnection
from app.models.email import EmailAccount
from app.models.social import SocialAccount
from app.models.conversation import Conversation, Message
from app.models.rag import RAGDocument

# Twin Models
from app.models.twin import (
    TwinProfileModel,
    TwinContactModel,
    TwinProjectModel,
    TwinLearningModel,
    TwinPatternModel,
    TwinActionModel,
)

# Unified Skill System Models
from app.models.skills import (
    Skill,
    SkillProposal,
    SkillRun,
    SkillType,
    SkillStatus
)

# MNEME Knowledge Base Models
from app.services.knowledge.models import (
    KnowledgeEntryModel,
    EmergentSkillModel,
    LearningHistoryModel,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "TenantMixin",
    "Tenant",
    "User",
    "OAuthConnection",
    "EmailAccount",
    "SocialAccount",
    "Conversation",
    "Message",
    "RAGDocument",
    # Twin
    "TwinProfileModel",
    "TwinContactModel",
    "TwinProjectModel",
    "TwinLearningModel",
    "TwinPatternModel",
    "TwinActionModel",
    # MNEME
    "KnowledgeEntryModel",
    "EmergentSkillModel",
    "LearningHistoryModel",
    # Skills
    "Skill",
    "SkillProposal",
    "SkillRun",
    "SkillType",
    "SkillStatus",
]
