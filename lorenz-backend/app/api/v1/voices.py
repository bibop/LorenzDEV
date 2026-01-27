"""
Voice API endpoints
Manage voices and personas for PersonaPlex
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import uuid
from pydub import AudioSegment
import io

from app.database import get_db
from app.models.voice import Voice, Persona
from app.schemas.voice import (
    VoiceCreate, VoiceUpdate, VoiceResponse,
    PersonaCreate, PersonaUpdate, PersonaResponse
)
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/voices", tags=["voices"])


# Voice endpoints
@router.get("", response_model=List[VoiceResponse])
async def list_voices(
    skip: int = 0,
    limit: int = 100,
    include_public: bool = True,
    include_system: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available voices"""
    query = db.query(Voice).filter(
        (Voice.tenant_id == current_user.tenant_id) | 
        (Voice.is_public == True) if include_public else False
    )
    
    if include_system:
        query = query.filter((Voice.is_system == True) | (Voice.created_by == current_user.id))
    
    voices = query.offset(skip).limit(limit).all()
    return voices


@router.post("", response_model=VoiceResponse, status_code=201)
async def create_voice(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload new voice sample
    Accepts WAV, MP3, or other audio formats
    """
    # Validate audio file
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Read audio file
    audio_data = await audio_file.read()
    
    # Get audio duration
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        duration_ms = len(audio)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")
    
    # Save audio file
    # TODO: Upload to S3 or file storage
    file_id = str(uuid.uuid4())
    audio_url = f"/storage/voices/{file_id}.wav"
    
    # TODO: Save audio_data to storage
    # For now, just store the path
    
    # Create voice record
    voice = Voice(
        name=name,
        description=description,
        audio_url=audio_url,
        duration_ms=duration_ms,
        created_by=current_user.id,
        tenant_id=current_user.tenant_id,
        is_public=is_public,
        is_system=False
    )
    
    db.add(voice)
    db.commit()
    db.refresh(voice)
    
    return voice


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get voice by ID"""
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    # Check permissions
    if voice.tenant_id != current_user.tenant_id and not voice.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return voice


@router.patch("/{voice_id}", response_model=VoiceResponse)
async def update_voice(
    voice_id: UUID,
    voice_update: VoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update voice metadata"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.created_by == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found or access denied")
    
    # Update fields
    for field, value in voice_update.dict(exclude_unset=True).items():
        setattr(voice, field, value)
    
    db.commit()
    db.refresh(voice)
    
    return voice


@router.delete("/{voice_id}", status_code=204)
async def delete_voice(
    voice_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete voice"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.created_by == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found or access denied")
    
    # Check if voice is used by personas
    persona_count = db.query(Persona).filter(Persona.voice_id == voice_id).count()
    if persona_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Voice is used by {persona_count} persona(s). Delete those first."
        )
    
    # TODO: Delete audio file from storage
    
    db.delete(voice)
    db.commit()
    
    return None


# Persona endpoints
@router.get("/personas", response_model=List[PersonaResponse])
async def list_personas(
    skip: int = 0,
    limit: int = 100,
    include_public: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available personas"""
    query = db.query(Persona).filter(
        (Persona.tenant_id == current_user.tenant_id) |
        (Persona.is_public == True) if include_public else False
    )
    
    personas = query.offset(skip).limit(limit).all()
    return personas


@router.post("/personas", response_model=PersonaResponse, status_code=201)
async def create_persona(
    persona: PersonaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new persona"""
    # Verify voice exists and is accessible
    voice = db.query(Voice).filter(Voice.id == persona.voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    if voice.tenant_id != current_user.tenant_id and not voice.is_public:
        raise HTTPException(status_code=403, detail="Voice access denied")
    
    # Create persona
    new_persona = Persona(
        **persona.dict(),
        created_by=current_user.id,
        tenant_id=current_user.tenant_id,
        is_system=False
    )
    
    db.add(new_persona)
    db.commit()
    db.refresh(new_persona)
    
    return new_persona


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get persona by ID"""
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    if persona.tenant_id != current_user.tenant_id and not persona.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return persona


@router.patch("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: UUID,
    persona_update: PersonaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update persona"""
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.created_by == current_user.id
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")
    
    # Update fields
    for field, value in persona_update.dict(exclude_unset=True).items():
        setattr(persona, field, value)
    
    db.commit()
    db.refresh(persona)
    
    return persona


@router.delete("/personas/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete persona"""
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.created_by == current_user.id
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found or access denied")
    
    db.delete(persona)
    db.commit()
    
    return None
