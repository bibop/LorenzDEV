"""
LORENZ SaaS - ElevenLabs Voice Service
========================================

Voice cloning and text-to-speech synthesis for the Digital Twin.
Uses ElevenLabs API for high-quality voice synthesis.
"""

import os
import logging
import aiohttp
from typing import Optional, Dict, Any, AsyncGenerator
from uuid import UUID
import hashlib

from app.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


class VoiceService:
    """
    ElevenLabs-based voice synthesis for Digital Twin.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2"
    ):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id  # User's cloned voice ID
        self.model_id = model_id
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self._session

    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def list_voices(self) -> list[Dict[str, Any]]:
        """List all available voices"""
        session = await self._get_session()
        async with session.get(f"{ELEVENLABS_API_BASE}/voices") as resp:
            if resp.status != 200:
                logger.error(f"Failed to list voices: {resp.status}")
                return []
            data = await resp.json()
            return data.get("voices", [])

    async def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get voice details"""
        session = await self._get_session()
        async with session.get(f"{ELEVENLABS_API_BASE}/voices/{voice_id}") as resp:
            if resp.status != 200:
                return None
            return await resp.json()

    async def create_voice_clone(
        self,
        name: str,
        audio_files: list[bytes],
        description: str = "LORENZ Digital Twin voice clone"
    ) -> Optional[str]:
        """
        Create a voice clone from audio samples.
        
        Args:
            name: Name for the cloned voice
            audio_files: List of audio file bytes (MP3/WAV)
            description: Voice description
            
        Returns:
            Voice ID or None on failure
        """
        session = await self._get_session()

        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field("name", name)
        data.add_field("description", description)

        for i, audio in enumerate(audio_files):
            data.add_field(
                "files",
                audio,
                filename=f"sample_{i}.mp3",
                content_type="audio/mpeg"
            )

        # Remove Content-Type header for multipart
        headers = {"xi-api-key": self.api_key}

        async with session.post(
            f"{ELEVENLABS_API_BASE}/voices/add",
            data=data,
            headers=headers
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                logger.error(f"Voice clone creation failed: {error}")
                return None

            result = await resp.json()
            voice_id = result.get("voice_id")
            logger.info(f"Created voice clone: {voice_id}")
            return voice_id

    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0
    ) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID to use (defaults to instance voice)
            stability: Voice stability (0-1)
            similarity_boost: Similarity to original voice (0-1)
            style: Style exaggeration (0-1)
            
        Returns:
            Audio bytes (MP3) or None on failure
        """
        voice = voice_id or self.voice_id
        if not voice:
            logger.error("No voice ID specified")
            return None

        session = await self._get_session()

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True
            }
        }

        async with session.post(
            f"{ELEVENLABS_API_BASE}/text-to-speech/{voice}",
            json=payload
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                logger.error(f"TTS failed: {error}")
                return None

            return await resp.read()

    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized speech in chunks.
        
        Yields audio chunks as they become available.
        """
        voice = voice_id or self.voice_id
        if not voice:
            logger.error("No voice ID specified")
            return

        session = await self._get_session()

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }

        async with session.post(
            f"{ELEVENLABS_API_BASE}/text-to-speech/{voice}/stream",
            json=payload
        ) as resp:
            if resp.status != 200:
                logger.error(f"TTS stream failed: {resp.status}")
                return

            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user/subscription info"""
        session = await self._get_session()
        async with session.get(f"{ELEVENLABS_API_BASE}/user") as resp:
            if resp.status != 200:
                return None
            return await resp.json()

    async def get_character_count(self) -> int:
        """Get remaining character count for current billing period"""
        info = await self.get_user_info()
        if not info:
            return 0
        subscription = info.get("subscription", {})
        return subscription.get("character_limit", 0) - subscription.get("character_count", 0)


# Singleton for app-wide usage
_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """Get or create voice service singleton"""
    global _voice_service
    if _voice_service is None:
        api_key = getattr(settings, "ELEVENLABS_API_KEY", None)
        if not api_key:
            api_key = os.getenv("ELEVENLABS_API_KEY")
        _voice_service = VoiceService(api_key=api_key)
    return _voice_service
