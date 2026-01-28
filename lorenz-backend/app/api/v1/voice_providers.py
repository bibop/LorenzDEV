"""
Voice provider routes
List available providers and their voices
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.voice_provider import VoiceProvider, PROVIDER_NAMES, PROVIDER_CAPABILITIES
from app.core.elevenlabs import get_elevenlabs_client
from app.core.personaplex import get_personaplex_client


router = APIRouter(prefix="/voice-providers", tags=["voice-providers"])


@router.get("/", response_model=List[Dict])
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """
    List all available voice providers with their capabilities
    """
    providers = []
    
    for provider in VoiceProvider:
        providers.append({
            "id": provider.value,
            "name": PROVIDER_NAMES[provider],
            "capabilities": PROVIDER_CAPABILITIES[provider],
            "enabled": True,  # TODO: Check if API keys are configured
        })
    
    return providers


@router.get("/{provider}/voices")
async def get_provider_voices(
    provider: VoiceProvider,
    current_user: User = Depends(get_current_user)
):
    """
    Get all available voices for a specific provider
    """
    if provider == VoiceProvider.ELEVENLABS:
        try:
            client = get_elevenlabs_client()
            voices = await client.get_voices()
            
            return [
                {
                    "id": v.voice_id,
                    "name": v.name,
                    "provider": "elevenlabs",
                    "category": v.category,
                    "description": v.description,
                    "preview_url": v.preview_url,
                    "labels": v.labels,
                }
                for v in voices
            ]
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"ElevenLabs API error: {str(e)}"
            )
    
    elif provider == VoiceProvider.PERSONAPLEX:
        try:
            client = get_personaplex_client()
            voices = await client.get_available_voices()
            
            return [
                {
                    "id": v["id"],
                    "name": v["name"],
                    "provider": "personaplex",
                    "description": v.get("description", ""),
                }
                for v in voices
            ]
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"PersonaPlex API error: {str(e)}"
            )
    
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")


@router.get("/{provider}/health")
async def check_provider_health(
    provider: VoiceProvider,
    current_user: User = Depends(get_current_user)
):
    """Check if provider API is accessible"""
    if provider == VoiceProvider.ELEVENLABS:
        client = get_elevenlabs_client()
        healthy = await client.health_check()
    elif provider == VoiceProvider.PERSONAPLEX:
        client = get_personaplex_client()
        healthy = await client.health_check()
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")
    
    return {
        "provider": provider.value,
        "healthy": healthy,
        "status": "online" if healthy else "offline"
    }
