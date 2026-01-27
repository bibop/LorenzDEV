"""
Voice library and persona templates
Default voices and personas for LORENZ
"""
from typing import List, Dict
from app.models.voice import Voice
from app.models.voice_provider import VoiceProvider


# Default system voices for PersonaPlex
PERSONAPLEX_SYSTEM_VOICES = [
    {
        "name": "Professional Assistant",
        "description": "Clear, professional voice suitable for business communications",
        "provider": VoiceProvider.PERSONAPLEX,
        "audio_url": "/voices/system/professional_assistant.wav",
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Friendly Helper",
        "description": "Warm, approachable voice for customer support",
        "provider": VoiceProvider.PERSONAPLEX,
        "audio_url": "/voices/system/friendly_helper.wav",
        "is_system": True,
        "is_public": True,
    },
]

# Default ElevenLabs voices (IDs from their API)
ELEVENLABS_SYSTEM_VOICES = [
    {
        "name": "Rachel",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "description": "Calm and professional American female voice",
        "provider": VoiceProvider.ELEVENLABS,
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Josh",
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",
        "description": "Young American male voice",
        "provider": VoiceProvider.ELEVENLABS,
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Bella",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "description": "Soft American female voice",
        "provider": VoiceProvider.ELEVENLABS,
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Antoni",
        "voice_id": "ErXwobaYiN019PkySvjV",
        "description": "Well-rounded American male voice",
        "provider": VoiceProvider.ELEVENLABS,
        "is_system": True,
        "is_public": True,
    },
]

# Persona templates
PERSONA_TEMPLATES = [
    {
        "name": "Customer Support Agent",
        "description": "Helpful and patient support specialist",
        "role_prompt": """You are a helpful and patient customer support agent. Your goal is to understand customer issues and provide clear, actionable solutions. Always be polite and empathetic.

Guidelines:
- Listen carefully to customer concerns
- Ask clarifying questions when needed
- Provide step-by-step solutions
- Offer to escalate complex issues
- End conversations with a satisfaction check""",
        "voice_name": "Rachel",
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Technical Expert",
        "description": "Knowledgeable tech specialist",
        "role_prompt": """You are a knowledgeable technical expert. Provide accurate, detailed technical information while explaining complex concepts in an understandable way. Use examples when helpful.

Guidelines:
- Use precise technical terminology
- Explain concepts clearly for non-experts
- Provide code examples when relevant
- Reference documentation when appropriate
- Admit when you don't know something""",
        "voice_name": "Josh",
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Creative Consultant",
        "description": "Enthusiastic creative brainstormer",
        "role_prompt": """You are an enthusiastic creative consultant. Help users brainstorm ideas, explore creative possibilities, and think outside the box. Be encouraging and inspiring.

Guidelines:
- Ask open-ended questions
- Build on user's ideas
- Suggest unexpected combinations
- Encourage experimentation
- Celebrate unique perspectives""",
        "voice_name": "Bella",
        "is_system": True,
        "is_public": True,
    },
    {
        "name": "Executive Assistant",
        "description": "Efficient professional assistant",
        "role_prompt": """You are a professional executive assistant. Help with scheduling, organization, and task management. Be concise, efficient, and proactive in offering solutions.

Guidelines:
- Prioritize tasks effectively
- Suggest time-saving approaches
- Keep responses concise
- Anticipate needs
- Maintain professional tone""",
        "voice_name": "Antoni",
        "is_system": True,
        "is_public": True,
    },
]


async def create_system_voices(db) -> List[Voice]:
    """Create system voices in database"""
    from app.models.voice import Voice
    
    voices = []
    
    # PersonaPlex voices
    for voice_data in PERSONAPLEX_SYSTEM_VOICES:
        voice = Voice(**voice_data)
        db.add(voice)
        voices.append(voice)
    
    # ElevenLabs voices (metadata only)
    for voice_data in ELEVENLABS_SYSTEM_VOICES:
        voice = Voice(**voice_data)
        db.add(voice)
        voices.append(voice)
    
    db.commit()
    return voices


async def create_system_personas(db, voices: List[Voice]):
    """Create system personas in database"""
    from app.models.voice import Persona
    
    personas = []
    voice_map = {v.name: v for v in voices}
    
    for template in PERSONA_TEMPLATES:
        voice = voice_map.get(template["voice_name"])
        if not voice:
            continue
        
        persona = Persona(
            name=template["name"],
            description=template["description"],
            role_prompt=template["role_prompt"],
            voice_id=voice.id,
            is_system=template["is_system"],
            is_public=template["is_public"],
        )
        db.add(persona)
        personas.append(persona)
    
    db.commit()
    return personas


async def initialize_voice_library(db):
    """Initialize complete voice library with system voices and personas"""
    voices = await create_system_voices(db)
    personas = await create_system_personas(db, voices)
    
    return {
        "voices": len(voices),
        "personas": len(personas),
    }
