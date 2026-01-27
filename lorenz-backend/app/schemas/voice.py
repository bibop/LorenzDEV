"""
Voice schemas for API requests/responses
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from uuid import UUID
from datetime import datetime


# Voice schemas
class VoiceBase(BaseModel):
    """Base voice schema"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_public: bool = False


class VoiceCreate(VoiceBase):
    """Create new voice (multipart with audio file)"""
    # audio_file will be handled separately in multipart form
    pass


class VoiceUpdate(BaseModel):
    """Update voice metadata"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class VoiceInDB(VoiceBase):
    """Voice in database"""
    id: UUID
    audio_url: str
    duration_ms: int
    created_by: UUID
    tenant_id: UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VoiceResponse(VoiceInDB):
    """Voice response for API"""
    pass


# Persona schemas
class PersonaBase(BaseModel):
    """Base persona schema"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    role_prompt: str = Field(..., description="Text prompt defining persona role/behavior")
    voice_id: UUID
    is_public: bool = False


class PersonaCreate(PersonaBase):
    """Create new persona"""
    pass


class PersonaUpdate(BaseModel):
    """Update persona"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    role_prompt: Optional[str] = None
    voice_id: Optional[UUID] = None
    is_public: Optional[bool] = None


class PersonaInDB(PersonaBase):
    """Persona in database"""
    id: UUID
    created_by: UUID
    tenant_id: UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PersonaResponse(PersonaInDB):
    """Persona response with voice details"""
    voice: VoiceResponse
    
    class Config:
        from_attributes = True


# Voice conversation schemas
class VoiceMessageCreate(BaseModel):
    """Send voice message"""
    conversation_id: UUID
    persona_id: Optional[UUID] = None  # Override conversation persona
    # audio_data will be in multipart form


class VoiceMessageResponse(BaseModel):
    """Voice message response"""
    message_id: UUID
    conversation_id: UUID
    transcript: str
    audio_url: str
    created_at: datetime
