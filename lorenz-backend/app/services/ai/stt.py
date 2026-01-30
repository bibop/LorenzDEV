"""
LORENZ - Speech to Text Service
Uses OpenAI Whisper for high-quality transcription
"""
import io
import os
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings

class STTService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set for STT")
        
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def transcribe(self, audio_data: bytes, language: str = "it") -> str:
        """
        Transcribe audio bytes using OpenAI Whisper
        Expects 16kHz Mono 16-bit PCM
        """
        import wave
        
        # Wrap raw PCM in a WAV container
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1) # Mono
            wav_file.setsampwidth(2) # 16-bit
            wav_file.setframerate(16000) # 16kHz
            wav_file.writeframes(audio_data)
        
        buffer.seek(0)
        buffer.name = "audio.wav"
        
        try:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=buffer,
                language=language
            )
            return response.text
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

_stt_service = None

def get_stt_service() -> STTService:
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
