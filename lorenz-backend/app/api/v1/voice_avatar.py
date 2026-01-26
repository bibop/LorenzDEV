"""
LORENZ SaaS - Digital Twin Voice & Avatar API
===============================================

Endpoints for voice synthesis and 3D avatar sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import io

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.twin.voice import VoiceService, get_voice_service
from app.services.twin.avatar import (
    AvatarSessionManager,
    AvatarSession,
    get_avatar_session_manager
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =====================
# Schemas
# =====================

class SynthesizeSpeechRequest(BaseModel):
    """Request to synthesize speech"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: Optional[str] = None
    stability: float = Field(0.5, ge=0, le=1)
    similarity_boost: float = Field(0.75, ge=0, le=1)
    style: float = Field(0.0, ge=0, le=1)


class VoiceCloneRequest(BaseModel):
    """Request to create voice clone"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class VoiceInfo(BaseModel):
    """Voice information"""
    voice_id: str
    name: str
    category: Optional[str] = None
    labels: Dict[str, str] = {}


class CreateSessionRequest(BaseModel):
    """Request to create avatar session"""
    voice_id: Optional[str] = None
    avatar_model: str = "default"
    metadata: Dict[str, Any] = {}


class SessionResponse(BaseModel):
    """Avatar session response"""
    session_id: str
    state: str
    voice_id: Optional[str] = None
    avatar_model: str
    created_at: str


class SDPOfferRequest(BaseModel):
    """SDP offer for WebRTC"""
    sdp: str


class ICECandidateRequest(BaseModel):
    """ICE candidate for WebRTC"""
    candidate: str
    sdpMid: Optional[str] = None
    sdpMLineIndex: Optional[int] = None


# =====================
# Voice Endpoints
# =====================

@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(
    current_user: User = Depends(get_current_user)
):
    """List available voices"""
    voice_service = get_voice_service()
    voices = await voice_service.list_voices()

    return [
        VoiceInfo(
            voice_id=v["voice_id"],
            name=v["name"],
            category=v.get("category"),
            labels=v.get("labels", {})
        )
        for v in voices
    ]


@router.post("/voice/synthesize")
async def synthesize_speech(
    request: SynthesizeSpeechRequest,
    current_user: User = Depends(get_current_user)
):
    """Synthesize speech from text"""
    voice_service = get_voice_service()

    audio = await voice_service.synthesize_speech(
        text=request.text,
        voice_id=request.voice_id,
        stability=request.stability,
        similarity_boost=request.similarity_boost,
        style=request.style
    )

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synthesize speech"
        )

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=speech.mp3"
        }
    )


@router.post("/voice/synthesize/stream")
async def synthesize_speech_stream(
    request: SynthesizeSpeechRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream synthesized speech"""
    voice_service = get_voice_service()

    async def audio_stream():
        async for chunk in voice_service.synthesize_stream(
            text=request.text,
            voice_id=request.voice_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost
        ):
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg"
    )


@router.get("/voice/quota")
async def get_voice_quota(
    current_user: User = Depends(get_current_user)
):
    """Get remaining voice synthesis quota"""
    voice_service = get_voice_service()
    remaining = await voice_service.get_character_count()

    return {
        "remaining_characters": remaining,
        "user_id": str(current_user.id)
    }


# =====================
# Avatar Session Endpoints
# =====================

@router.post("/avatar/session", response_model=SessionResponse)
async def create_avatar_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new avatar session"""
    manager = get_avatar_session_manager()

    session = await manager.create_session(
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        voice_id=request.voice_id,
        avatar_model=request.avatar_model,
        metadata=request.metadata
    )

    return SessionResponse(
        session_id=session.session_id,
        state=session.state.value,
        voice_id=session.voice_id,
        avatar_model=session.avatar_model,
        created_at=session.created_at.isoformat()
    )


@router.get("/avatar/session/{session_id}", response_model=SessionResponse)
async def get_avatar_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get avatar session status"""
    manager = get_avatar_session_manager()
    session = await manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify ownership
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )

    return SessionResponse(
        session_id=session.session_id,
        state=session.state.value,
        voice_id=session.voice_id,
        avatar_model=session.avatar_model,
        created_at=session.created_at.isoformat()
    )


@router.delete("/avatar/session/{session_id}")
async def end_avatar_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """End an avatar session"""
    manager = get_avatar_session_manager()
    session = await manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    await manager.end_session(session_id)
    return {"message": "Session ended", "session_id": session_id}


@router.post("/avatar/session/{session_id}/offer")
async def set_sdp_offer(
    session_id: str,
    request: SDPOfferRequest,
    current_user: User = Depends(get_current_user)
):
    """Set SDP offer for WebRTC negotiation"""
    manager = get_avatar_session_manager()
    session = await manager.get_session(session_id)

    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    success = await manager.set_sdp_offer(session_id, request.sdp)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set offer")

    return {"message": "Offer received", "session_id": session_id}


@router.get("/avatar/session/{session_id}/answer")
async def get_sdp_answer(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get SDP answer for WebRTC negotiation"""
    manager = get_avatar_session_manager()
    session = await manager.get_session(session_id)

    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.sdp_answer:
        raise HTTPException(status_code=425, detail="Answer not ready yet")

    return {"sdp": session.sdp_answer}


@router.post("/avatar/session/{session_id}/ice-candidate")
async def add_ice_candidate(
    session_id: str,
    request: ICECandidateRequest,
    current_user: User = Depends(get_current_user)
):
    """Add ICE candidate for WebRTC"""
    manager = get_avatar_session_manager()
    session = await manager.get_session(session_id)

    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    await manager.add_ice_candidate(
        session_id,
        {
            "candidate": request.candidate,
            "sdpMid": request.sdpMid,
            "sdpMLineIndex": request.sdpMLineIndex
        },
        from_client=True
    )

    return {"message": "ICE candidate added"}


@router.get("/avatar/sessions")
async def list_my_sessions(
    current_user: User = Depends(get_current_user)
):
    """List user's avatar sessions"""
    manager = get_avatar_session_manager()
    sessions = await manager.get_user_sessions(str(current_user.id))

    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }
