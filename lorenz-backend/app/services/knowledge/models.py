"""
LORENZ SaaS - MNEME Database Models
====================================

SQLAlchemy models for knowledge base storage.
Multi-tenant knowledge management for LORENZ SaaS.
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base, TimestampMixin


class KnowledgeEntryModel(Base):
    """
    Knowledge entry in MNEME

    Categories:
    - pattern: Learned interaction patterns
    - workflow: Discovered workflow combinations
    - fact: Facts about user/context
    - preference: User preferences
    - skill_memory: Skill execution memories
    """
    __tablename__ = "knowledge_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    context = Column(JSON, default={})

    # Metadata
    access_count = Column(Integer, default=0)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    source = Column(String(100), default="")  # "conversation", "skill", "user_input"
    tags = Column(JSON, default=[])
    related_skills = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Embedding for semantic search (optional)
    embedding_id = Column(String(100), nullable=True)  # Qdrant point ID

    def to_dict(self):
        return {
            "id": str(self.id),
            "category": self.category,
            "title": self.title,
            "content": self.content,
            "context": self.context,
            "access_count": self.access_count,
            "confidence": self.confidence,
            "source": self.source,
            "tags": self.tags,
            "related_skills": self.related_skills,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmergentSkillModel(Base):
    """
    Emergent skills learned by LORENZ

    These are user-specific automation patterns that LORENZ
    discovers through repeated interactions.
    """
    __tablename__ = "emergent_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text)
    description_it = Column(Text)

    # Skill definition
    trigger_patterns = Column(JSON, default=[])  # Phrases that trigger this skill
    workflow_steps = Column(JSON, default=[])  # Steps to execute
    category = Column(String(50), default="custom")

    # Metadata
    use_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    enabled = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    created_from = Column(String(255), default="")  # Context of creation

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "description_it": self.description_it,
            "trigger_patterns": self.trigger_patterns,
            "workflow_steps": self.workflow_steps,
            "category": self.category,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "enabled": self.enabled,
            "tags": self.tags,
            "created_from": self.created_from,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LearningHistoryModel(Base):
    """
    Learning history tracking

    Records how LORENZ learns from interactions
    for transparency and debugging.
    """
    __tablename__ = "learning_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)  # "pattern_learned", "skill_created", "knowledge_added"
    skill_name = Column(String(100), nullable=True)
    input_text = Column(Text)
    result_success = Column(Boolean, default=True)
    learned_pattern = Column(Text)
    context = Column(JSON, default={})

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "skill_name": self.skill_name,
            "input_text": self.input_text,
            "result_success": self.result_success,
            "learned_pattern": self.learned_pattern,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
