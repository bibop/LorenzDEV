"""
Voice provider enum and constants
Supports multiple TTS providers (PersonaPlex, ElevenLabs, etc.)
"""
from enum import Enum


class VoiceProvider(str, Enum):
    """Supported voice providers"""
    PERSONAPLEX = "personaplex"
    ELEVENLABS = "elevenlabs"
    # Future: GOOGLE_TTS = "google_tts"
    # Future: AZURE_TTS = "azure_tts"


# Provider display names
PROVIDER_NAMES = {
    VoiceProvider.PERSONAPLEX: "Nvidia PersonaPlex",
    VoiceProvider.ELEVENLABS: "ElevenLabs",
}

# Provider capabilities
PROVIDER_CAPABILITIES = {
    VoiceProvider.PERSONAPLEX: {
        "full_duplex": True,
        "voice_cloning": True,
        "custom_upload": True,
        "streaming": True,
        "latency_ms": 70,
    },
    VoiceProvider.ELEVENLABS: {
        "full_duplex": False,
        "voice_cloning": True,
        "custom_upload": False,  # Requires Pro plan
        "streaming": True,
        "latency_ms": 150,
    },
}
