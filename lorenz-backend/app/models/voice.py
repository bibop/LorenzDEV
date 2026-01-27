"""
Voice model for PersonaPlex integration
Stores custom voice samples and configurations
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base


class Voice(Base):
    """Voice sample for PersonaPlex"""
    __tablename__ = "voices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Audio file reference
    audio_url = Column(Text, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Visibility
    is_public = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System-provided voices
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="voices")
    tenant = relationship("Tenant")
    personas = relationship("Persona", back_populates="voice")


class Persona(Base):
    """AI Persona configuration (role + voice)"""
    __tablename__ = "personas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Persona configuration
    role_prompt = Column(Text, nullable=False)  # Text prompt defining role/behavior
    voice_id = Column(UUID(as_uuid=True), ForeignKey("voices.id"), nullable=False)
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Visibility
    is_public = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System-provided personas
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    voice = relationship("Voice", back_populates="personas")
    creator = relationship("User", back_populates="personas")
    tenant = relationship("Tenant")
    conversations = relationship("Conversation", back_populates="persona")
