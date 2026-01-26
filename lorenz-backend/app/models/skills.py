"""
LORENZ SaaS - Skill Models
"""

from sqlalchemy import Column, String, Boolean, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin, TenantMixin


class SkillType(str, enum.Enum):
    GOD = "god"
    EMERGENT = "emergent"


class SkillStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class Skill(Base, TimestampMixin, TenantMixin):
    """
    Registry unique for all LORENZ skills (God + Emergent).
    """
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    skill_type = Column(SQLEnum(SkillType), default=SkillType.GOD, nullable=False)
    status = Column(SQLEnum(SkillStatus), default=SkillStatus.ACTIVE, nullable=False)
    
    # Configuration & Metadata
    category = Column(String(50), nullable=True)
    icon = Column(String(10), nullable=True) # Emoji or icon name
    version = Column(String(20), default="1.0.0")
    
    # JSON schema for tools (compatible with OpenAI/Anthropic tool call specs)
    tool_schema = Column(JSONB, nullable=False)
    
    # Implementation details (for emergent skills, this might be a reference to a script or LLM prompt)
    implementation = Column(JSONB, nullable=True)
    
    # Runtime stats
    use_count = Column(Float, default=0)
    success_rate = Column(Float, default=1.0)
    avg_latency_ms = Column(Float, default=0.0)

    # Relationships
    runs = relationship("SkillRun", back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Skill {self.name} ({self.skill_type})>"


class SkillProposal(Base, TimestampMixin, TenantMixin):
    """
    Proposed emergent skills learned from Pattern Miner.
    Requires human review before becoming a 'Skill'.
    """
    __tablename__ = "skill_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggested_name = Column(String(100), nullable=False)
    reasoning = Column(Text, nullable=False) # Why this pattern was extracted
    confidence = Column(Float, nullable=False)
    
    # The draft implementation/schema
    proposed_schema = Column(JSONB, nullable=False)
    
    status = Column(String(20), default="pending") # pending, approved, rejected
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Telemetry that triggered this proposal
    pattern_data = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<SkillProposal {self.suggested_name} (conf: {self.confidence})>"


class SkillRun(Base, TimestampMixin, TenantMixin):
    """
    Audit log and telemetry for every skill execution.
    Target: RSI telemetry and accountability.
    """
    __tablename__ = "skill_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    
    # Inputs/Outputs
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    
    # Performance
    latency_ms = Column(Float, nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # RSI Feedback
    user_feedback = Column(JSONB, nullable=True) # {score: 1-5, comment: "..."}

    skill = relationship("Skill", back_populates="runs")

    def __repr__(self):
        return f"<SkillRun {self.skill_id} (success: {self.success})>"
