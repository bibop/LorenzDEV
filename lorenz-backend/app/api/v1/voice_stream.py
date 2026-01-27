"""
Voice WebSocket endpoint for real-time voice streaming
Handles bidirectional audio communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
import json

from app.core.personaplex import get_personaplex_client
from app.core.elevenlabs import get_elevenlabs_client
from app.models.voice_provider import VoiceProvider


router = APIRouter()


class VoiceStreamHandler:
    """Handles voice streaming session"""
    
    def __init__(
        self,
        websocket: WebSocket,
        conversation_id: str,
        provider: str,
        voice_id: Optional[str] = None,
        persona_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.conversation_id = conversation_id
        self.provider = VoiceProvider(provider)
        self.voice_id = voice_id
        self.persona_id = persona_id
        self.is_active = False
    
    async def start(self):
        """Start voice streaming session"""
        self.is_active = True
        
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
        """Handle ElevenLabs streaming (ping-pong)"""
        client = get_elevenlabs_client()
        
        try:
            # ElevenLabs is not full-duplex, so we do ping-pong
            while self.is_active:
                # Receive user audio
                audio_data = await self.receive_audio_chunk()
                if not audio_data:
                    break
                
                # Transcribe (if needed)
                # TODO: Add speech-to-text
                
                # Generate response (text-to-speech)
                # TODO: Get text response from LLM
                response_text = "This is a demo response"
                
                # Stream TTS response
                async for audio_chunk in client.text_to_speech_stream(
                    text=response_text,
                    voice_id=self.voice_id or "21m00Tcm4TlvDq8ikWAM"
                ):
                    await self.send_audio(audio_chunk)
        
        except Exception as e:
            await self.send_error(f"ElevenLabs error: {str(e)}")
    
    async def receive_audio(self):
        """Receive audio from client"""
        try:
            while self.is_active:
                data = await self.websocket.receive()
                
                if "bytes" in data:
                    # Audio data
                    audio_chunk = data["bytes"]
                    # TODO: Process audio chunk
                    pass
                
                elif "text" in data:
                    # Control message
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
        
        if action == "mute":
            # Pause processing
            pass
        elif action == "unmute":
            # Resume processing
            pass
        elif action == "end":
            self.is_active = False
    
    def stop(self):
        """Stop streaming session"""
        self.is_active = False


@router.websocket("/voice/stream")
async def voice_stream(
    websocket: WebSocket,
    conversation_id: str = Query(...),
    provider: str = Query(...),
    voice_id: Optional[str] = Query(None),
    persona_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time voice streaming
    
    Supports:
    - PersonaPlex: Full-duplex conversation
    - ElevenLabs: Ping-pong TTS
    """
    await websocket.accept()
    
    handler = VoiceStreamHandler(
        websocket=websocket,
        conversation_id=conversation_id,
        provider=provider,
        voice_id=voice_id,
        persona_id=persona_id
    )
    
    try:
        await handler.start()
    except WebSocketDisconnect:
        print(f"Client disconnected from voice stream: {conversation_id}")
    except Exception as e:
        print(f"Voice stream error: {e}")
        try:
            await handler.send_error(str(e))
        except:
            pass
    finally:
        handler.stop()
