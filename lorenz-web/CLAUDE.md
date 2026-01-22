# CLAUDE.md - lorenz-web

This file provides guidance to Claude Code when working with the LORENZ web frontend.

## Project Overview

**lorenz-web** is the Next.js 14 web dashboard for LORENZ, a multi-tenant SaaS AI personal assistant platform. It provides:
- User authentication (login/register)
- Dashboard with chat interface
- Email management
- Knowledge base management
- Twin configuration and skills
- Immersive voice-based onboarding with animated Orb

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **Animation**: Framer Motion
- **3D/Canvas**: Three.js + React Three Fiber (for some components)
- **State**: Zustand
- **Backend**: Connects to FastAPI backend at `http://localhost:8000`

## Essential Commands

```bash
# Install dependencies
npm install

# Development server (port 3000)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Project Structure

```
lorenz-web/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Landing page (redirects to login)
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── setup/             # Initial setup wizard
│   ├── onboarding/        # Text-based onboarding
│   ├── onboarding-orb/    # Voice-based immersive onboarding
│   ├── dashboard/         # Main dashboard (protected)
│   │   ├── layout.tsx     # Dashboard layout with sidebar
│   │   ├── page.tsx       # Dashboard home
│   │   ├── chat/          # AI chat interface
│   │   ├── email/         # Email management
│   │   ├── twin/          # Twin configuration
│   │   ├── knowledge/     # Knowledge base
│   │   ├── skills/        # Skills management
│   │   ├── documents/     # Document management
│   │   └── settings/      # User settings
│   └── demo/
│       └── voice-orb/     # Voice Orb demo page
├── components/
│   ├── ui/                # shadcn/ui components + custom UI
│   │   ├── conversation.tsx   # Chat conversation display
│   │   ├── message.tsx        # Individual message
│   │   ├── voice-button.tsx   # Voice input button
│   │   └── shimmering-text.tsx # Text animation effect
│   ├── voice/             # Voice-related components
│   │   ├── VoiceOrb.tsx   # Three.js animated orb
│   │   └── useAudioAnalyzer.ts # Audio analysis hook
│   ├── setup/             # Setup wizard components
│   └── LorenzOrb.tsx      # Canvas-based animated orb with TTS/STT
├── lib/
│   ├── api.ts             # API client for backend
│   └── utils.ts           # Utility functions (cn, etc.)
├── hooks/                 # Custom React hooks
├── styles/                # Global styles
└── types/                 # TypeScript type definitions
```

## Key Components

### LorenzOrb (`components/LorenzOrb.tsx`)
Canvas-animated orb with states: idle, speaking, listening, thinking, success, error.
- Uses Web Speech API for TTS (SpeechSynthesis)
- Speech Recognition for voice input
- Framer Motion for position animations
- Includes `useLorenzOrb` hook for controlling the orb

### VoiceOrb (`components/voice/VoiceOrb.tsx`)
Three.js-based 3D animated orb using React Three Fiber.
- Real-time audio visualization
- Shader-based effects

### Chat Interface (`app/dashboard/chat/page.tsx`)
Main AI conversation interface:
- Markdown rendering
- Streaming responses
- Voice input support

## API Integration

Backend URL is configured via `NEXT_PUBLIC_API_URL` environment variable (default: `http://localhost:8000`).

API client in `lib/api.ts` handles:
- Authentication (JWT tokens)
- Chat messages
- Email operations
- Twin/knowledge management

### Key Endpoints Used

```typescript
// Auth
POST /api/v1/auth/login
POST /api/v1/auth/register

// Chat
POST /api/v1/chat/message

// Twin
POST /api/v1/twin/chat
GET  /api/v1/twin/emails

// Onboarding
POST /api/v1/onboarding/identity/discover
POST /api/v1/onboarding/identity/complete
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Multi-tenant Architecture

The platform supports multiple users with strict data isolation:
- Each user has their own Twin (AI assistant)
- Knowledge bases are tenant-isolated
- Email accounts are per-user

## Voice Interaction

The onboarding flow uses voice for all interactions:
- **TTS**: Web Speech API SpeechSynthesis (Italian voice)
- **STT**: Web Speech API SpeechRecognition
- Orb animates based on speaking/listening state

## Adding New Pages

1. Create directory in `app/` following App Router conventions
2. Add `page.tsx` with 'use client' directive if using client features
3. Use existing UI components from `components/ui/`

## Adding New Components

1. For UI primitives: use shadcn/ui pattern in `components/ui/`
2. For feature components: create in appropriate subdirectory
3. Always use TypeScript with proper interfaces

## Styling Guidelines

- Use Tailwind CSS utility classes
- Dark theme is default (dark mode classes)
- Use `cn()` utility for conditional classes
- Follow existing component patterns

## Related Projects

- **lorenz-backend**: FastAPI backend at `/Users/bibop/Documents/AI/Lorenz/lorenz-backend`
- **Main LORENZ docs**: `/Users/bibop/Documents/AI/Lorenz/CLAUDE.md`
