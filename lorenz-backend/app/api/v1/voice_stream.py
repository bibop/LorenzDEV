"""
Voice WebSocket endpoint for real-time voice streaming
Handles bidirectional audio communication with Twin integration
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import asyncio
import json
import logging

from app.database import get_db, set_tenant_context
from app.config import settings
from app.models import User
from app.core.personaplex import get_personaplex_client
from app.core.elevenlabs import get_elevenlabs_client
from app.models.voice_provider import VoiceProvider
from app.services.twin import get_twin_service, TwinService
from app.services.ai.stt import get_stt_service
from jose import jwt, JWTError
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_ws(token: str, db: AsyncSession) -> User:
    """Authentication for WebSocket"""
    # #!!MOCK!!# Development bypass
    if settings.DEBUG and token == "test_token":
        from uuid import UUID
        mock_user = User(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="test@lorenz.ai",
            name="Test User",
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            role="owner",
            is_active=True,
            email_verified=True
        )
        await set_tenant_context(db, str(mock_user.tenant_id))
        return mock_user
    # #!!END_MOCK!!#

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    await set_tenant_context(db, str(user.tenant_id))
    return user


class VoiceStreamHandler:
    """Handles voice streaming session"""
    
    def __init__(
        self,
        websocket: WebSocket,
        conversation_id: str,
        provider: str,
        user: User,
        db: AsyncSession,
        voice_id: Optional[str] = None,
        persona_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.conversation_id = conversation_id
        self.provider = VoiceProvider(provider)
        self.user = user
        self.db = db
        self.voice_id = voice_id
        self.persona_id = persona_id
        self.is_active = False
        self.twin: Optional[TwinService] = None
        self.audio_buffer = bytearray()
        self.stt = get_stt_service()
    
    async def start(self):
        """Start voice streaming session"""
        self.is_active = True
        
        # Initialize Twin Service
        try:
            self.twin = await get_twin_service(self.user, self.db)
            logger.info(f"Twin initialized for voice session: {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Twin: {e}")
            await self.send_error("Failed to initialize AI Brain")
            return

        if self.provider == VoiceProvider.PERSONAPLEX:
            await self.handle_personaplex()
        elif self.provider == VoiceProvider.ELEVENLABS:
            await self.handle_elevenlabs()
    
    async def handle_personaplex(self):
        """Handle PersonaPlex full-duplex streaming"""
        client = get_personaplex_client()
        
        try:
            # PersonaPlex supports full-duplex, so we can send and receive simultaneously
            receive_task = asyncio.create_task(self.receive_audio())
            send_task = asyncio.create_task(self.send_to_personaplex(client))
            
            await asyncio.gather(receive_task, send_task)
        except Exception as e:
            await self.send_error(f"PersonaPlex error: {str(e)}")
    
    async def handle_elevenlabs(self):
        """Handle ElevenLabs streaming (ping-pong) with VAD"""
        client = get_elevenlabs_client()
        import audioop
        
        # VAD Parameters
        THRESHOLD = 1000  # RMS threshold for silence
        SILENCE_LIMIT = 30  # ~0.5s silence
        
        silence_frames = 0
        is_speaking = False
        
        try:
            while self.is_active:
                # Receive user audio
                audio_chunk = await self.receive_audio_chunk()
                if not audio_chunk:
                    break
                
                # Add to buffer
                self.audio_buffer.extend(audio_chunk)
                
                # Calculate RMS (Energy) for VAD
                try:
                    rms = audioop.rms(audio_chunk, 2) # Assume 16-bit
                except Exception:
                    rms = 0

                if rms > THRESHOLD:
                    is_speaking = True
                    silence_frames = 0
                else:
                    if is_speaking:
                        silence_frames += 1

                # Trigger response after silence
                if is_speaking and silence_frames > SILENCE_LIMIT:
                    is_speaking = False
                    silence_frames = 0
                    
                    # 1. Real STT (using OpenAI Whisper)
                    if len(self.audio_buffer) > 3200: # At least 0.1s of audio
                        logger.info(f"Transcribing {len(self.audio_buffer)} bytes of audio...")
                        transcript = await self.stt.transcribe(bytes(self.audio_buffer))
                        self.audio_buffer.clear() # Reset buffer for next turn
                        
                        if transcript.strip():
                            logger.info(f"STT Transcript: {transcript}")
                            await self.send_transcript(transcript, is_user=True)
                            
                            # 2. Get Brain Response
                            try:
                                response_text = await self.twin.process_message(transcript)
                                logger.info(f"Twin Response: {response_text[:50]}...")
                                await self.send_transcript(response_text, is_user=False)
                                
                                # 3. Stream TTS Response
                                async for playback_chunk in client.text_to_speech_stream(
                                    text=response_text,
                                    voice_id=self.voice_id or "21m00Tcm4TlvDq8ikWAM",
                                    output_format="pcm_24000"
                                ):
                                    if not self.is_active: break
                                    await self.send_audio(playback_chunk)
                            except Exception as e:
                                logger.error(f"Brain/TTS processing error: {e}")
                                await self.send_error("AI encountered an error processing your request")
                        else:
                            logger.warning("Empty transcript received")
        
        except Exception as e:
            await self.send_error(f"ElevenLabs error: {str(e)}")
    
    async def receive_audio(self):
        """Receive audio from client"""
        try:
            while self.is_active:
                data = await self.websocket.receive()
                
                if "bytes" in data:
                    pass # Handled in receive_audio_chunk for simple flow
                
                elif "text" in data:
                    message = json.loads(data["text"])
                    if message.get("type") == "control":
                        await self.handle_control(message)
        
        except WebSocketDisconnect:
            self.is_active = False
    
    async def receive_audio_chunk(self) -> Optional[bytes]:
        """Receive single audio chunk"""
        try:
            data = await self.websocket.receive()
            if "bytes" in data:
                return data["bytes"]
            if "text" in data:
                # Check for control messages interleaved
                pass 
        except WebSocketDisconnect:
            self.is_active = False
        return None
    
    async def send_to_personaplex(self, client):
        """Stream audio to PersonaPlex and receive responses"""
        # TODO: Implement PersonaPlex streaming
        pass
    
    async def send_audio(self, audio_data: bytes):
        """Send audio to client"""
        await self.websocket.send_bytes(audio_data)
    
    async def send_transcript(self, text: str, is_user: bool = False):
        """Send transcript to client"""
        message = {
            "type": "transcript",
            "data": {
                "text": text,
                "is_user": is_user
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.websocket.send_text(json.dumps(message))
    
    async def send_error(self, error: str):
        """Send error to client"""
        message = {
            "type": "error",
            "data": {"error": error},
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.websocket.send_text(json.dumps(message))
    
    async def handle_control(self, message: dict):
        """Handle control messages"""
        action = message.get("data", {}).get("action")
        if action == "end":
            self.is_active = False
    
    def stop(self):
        """Stop streaming session"""
        self.is_active = False


@router.websocket("/voice/stream")
async def voice_stream(
    websocket: WebSocket,
    conversation_id: str = Query(...),
    provider: str = Query(...),
    token: str = Query(...),
    voice_id: Optional[str] = Query(None),
    persona_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time voice streaming with AI Brain integration
    """
    try:
        user = await get_current_user_ws(token, db)
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    
    handler = VoiceStreamHandler(
        websocket=websocket,
        conversation_id=conversation_id,
        provider=provider,
        user=user,
        db=db,
        voice_id=voice_id,
        persona_id=persona_id
    )
    
    try:
        await handler.start()
    except WebSocketDisconnect:
        print(f"Client disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"Voice stream error: {e}")
        try:
            await handler.send_error(str(e))
        except:
            pass
    finally:
        handler.stop()
