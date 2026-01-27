# Voice Library Initialization

This directory contains scripts for initializing the LORENZ voice library.

## Usage

### Initialize System Voices and Personas

```bash
cd lorenz-backend
python -m app.scripts.init_voice_library
```

This will create:
- **System Voices** (PersonaPlex + ElevenLabs defaults)
- **Persona Templates** (Customer Support, Technical Expert, Creative Consultant, Executive Assistant)

## System Voices

### PersonaPlex
- Professional Assistant
- Friendly Helper

### ElevenLabs
- Rachel (Calm professional female)
- Josh (Young male)
- Bella (Soft female)
- Antoni (Well-rounded male)

## Persona Templates

Each template includes:
- Name and description
- Complete role prompt with guidelines
- Recommended voice
- Public visibility

Run this script after database migration to populate the initial library.
