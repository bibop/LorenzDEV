"""
ElevenLabs API Client
Handles communication with ElevenLabs TTS API
"""
from typing import List, Optional, Dict
import httpx
import os


class ElevenLabsVoice:
    """ElevenLabs voice model"""
    def __init__(self, data: dict):
        self.voice_id = data["voice_id"]
        self.name = data["name"]
        self.category = data.get("category", "")
        self.description = data.get("description", "")
        self.preview_url = data.get("preview_url")
        self.labels = data.get("labels", {})


class ElevenLabsClient:
    """Client for ElevenLabs API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.client = httpx.AsyncClient(
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=30
        )
    
    async def get_voices(self) -> List[ElevenLabsVoice]:
        """Get all available voices"""
        response = await self.client.get(f"{self.base_url}/voices")
        response.raise_for_status()
        
        data = response.json()
        return [ElevenLabsVoice(v) for v in data.get("voices", [])]
    
    async def get_voice(self, voice_id: str) -> ElevenLabsVoice:
        """Get specific voice details"""
        response = await self.client.get(f"{self.base_url}/voices/{voice_id}")
        response.raise_for_status()
        return ElevenLabsVoice(response.json())
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_monolingual_v1",
        voice_settings: Optional[Dict] = None
    ) -> bytes:
        """
        Convert text to speech
        Returns audio data as bytes
        """
        if voice_settings is None:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings
        }
        
        response = await self.client.post(
            f"{self.base_url}/text-to-speech/{voice_id}",
            json=payload
        )
        response.raise_for_status()
        
        return response.content
    
    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_monolingual_v1"
    ):
        """
        Stream text to speech (for real-time playback)
        Yields audio chunks
        """
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/text-to-speech/{voice_id}/stream",
            json=payload
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
    
    async def clone_voice(
        self,
        name: str,
        files: List[bytes],
        description: Optional[str] = None
    ) -> str:
        """
        Clone a voice from audio samples
        Returns voice_id of cloned voice
        Requires Pro plan
        """
        # Prepare multipart form data
        files_data = [
            ("files", (f"sample_{i}.mp3", data, "audio/mpeg"))
            for i, data in enumerate(files)
        ]
        
        data = {"name": name}
        if description:
            data["description"] = description
        
        response = await self.client.post(
            f"{self.base_url}/voices/add",
            files=files_data,
            data=data
        )
        response.raise_for_status()
        
        result = response.json()
        return result["voice_id"]
    
    async def delete_voice(self, voice_id: str):
        """Delete a cloned voice"""
        response = await self.client.delete(f"{self.base_url}/voices/{voice_id}")
        response.raise_for_status()
    
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        try:
            response = await self.client.get(f"{self.base_url}/voices")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global client instance
_elevenlabs_client: Optional[ElevenLabsClient] = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """Get or create ElevenLabs client singleton"""
    global _elevenlabs_client
    
    if _elevenlabs_client is None:
        _elevenlabs_client = ElevenLabsClient()
    
    return _elevenlabs_client
