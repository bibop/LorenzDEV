"""
PersonaPlex Client Wrapper
Handles communication with PersonaPlex server
"""
from typing import Optional, List
import httpx
import asyncio
from pydantic import BaseModel


class VoicePrompt(BaseModel):
    """Voice characteristics from audio sample"""
    audio_url: str
    duration_ms: int


class PersonaConfig(BaseModel):
    """Persona role and behavior"""
    role_prompt: str
    voice_prompt: VoicePrompt


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    audio_url: Optional[str] = None


class PersonaPlexClient:
    """Client for PersonaPlex server"""
    
    def __init__(self, server_url: str, timeout: int = 30):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def create_conversation(
        self,
        persona: PersonaConfig,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Initialize a new conversation with a persona
        Returns conversation_id
        """
        response = await self.client.post(
            f"{self.server_url}/conversations",
            json={
                "conversation_id": conversation_id,
                "persona": persona.dict()
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["conversation_id"]
    
    async def send_message(
        self,
        conversation_id: str,
        audio_data: bytes,
        format: str = "wav"
    ) -> ConversationMessage:
        """
        Send audio message and get response
        Full-duplex: can interrupt and get immediate response
        """
        files = {
            "audio": (f"input.{format}", audio_data, f"audio/{format}")
        }
        data = {
            "conversation_id": conversation_id
        }
        
        response = await self.client.post(
            f"{self.server_url}/messages",
            files=files,
            data=data
        )
        response.raise_for_status()
        return ConversationMessage(**response.json())
    
    async def stream_conversation(
        self,
        conversation_id: str,
        audio_stream
    ):
        """
        Stream audio in real-time (WebSocket or Server-Sent Events)
        For full-duplex conversation
        """
        # TODO: Implement WebSocket streaming
        pass
    
    async def get_available_voices(self) -> List[dict]:
        """Get list of available pre-configured voices"""
        response = await self.client.get(f"{self.server_url}/voices")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> bool:
        """Check if PersonaPlex server is healthy"""
        try:
            response = await self.client.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global client instance
_personaplex_client: Optional[PersonaPlexClient] = None


def get_personaplex_client() -> PersonaPlexClient:
    """Get or create PersonaPlex client singleton"""
    global _personaplex_client
    
    if _personaplex_client is None:
        from app.config import settings
        server_url = settings.PERSONAPLEX_URL
        _personaplex_client = PersonaPlexClient(server_url)
    
    return _personaplex_client
