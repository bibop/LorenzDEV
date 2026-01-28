"""
Simple TTS endpoint for testing
Converts text to speech and returns audio file
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.elevenlabs import get_elevenlabs_client
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel


@router.post("/tts/generate")
async def generate_tts(
    request: TTSRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate TTS audio from text
    Returns MP3 audio file
    """
    try:
        client = get_elevenlabs_client()
        
        # Generate audio
        audio_data = await client.text_to_speech(
            text=request.text,
            voice_id=request.voice_id
        )
        
        # Return audio as MP3
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=tts.mp3"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )
