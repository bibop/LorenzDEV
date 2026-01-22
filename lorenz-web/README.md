# LORENZ SaaS - Web Dashboard

Modern Next.js web dashboard for the LORENZ AI Personal Assistant platform.

## Features

- **Chat Interface**: Real-time conversation with LORENZ AI
- **MNEME Knowledge Base**: Manage persistent memory and learned patterns
- **Skills Dashboard**: Execute and manage AI skills
- **Email Integration**: View and manage connected email accounts
- **User Settings**: Profile, integrations, notifications, and security

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS with custom theme
- **UI Components**: Radix UI primitives
- **State Management**: Zustand
- **Icons**: Lucide React
- **Markdown**: React Markdown

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Running LORENZ backend API

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with your configuration
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
lorenz-web/
├── app/                    # Next.js App Router
│   ├── dashboard/          # Protected dashboard routes
│   │   ├── chat/           # Chat interface
│   │   ├── knowledge/      # MNEME knowledge base
│   │   ├── skills/         # Skills management
│   │   ├── email/          # Email client
│   │   └── settings/       # User settings
│   ├── login/              # Authentication
│   ├── register/           # User registration
│   └── page.tsx            # Home (redirect)
├── components/             # React components
│   ├── ui/                 # Reusable UI components
│   ├── chat/               # Chat-specific components
│   ├── knowledge/          # Knowledge base components
│   └── dashboard/          # Dashboard components
├── lib/                    # Utilities
│   ├── api.ts              # API client
│   └── utils.ts            # Helper functions
├── types/                  # TypeScript types
├── styles/                 # Global styles
└── hooks/                  # Custom React hooks
```

## API Integration

The dashboard connects to the LORENZ FastAPI backend. Configure the API URL in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Customization

### Theme

Edit `tailwind.config.js` to customize the color scheme. The LORENZ theme uses:

- Primary: Indigo (#6366f1)
- Secondary: Violet (#8b5cf6)
- Accent: Cyan (#06b6d4)

### Adding New Pages

1. Create a new folder in `app/dashboard/`
2. Add a `page.tsx` file
3. Update the navigation in `app/dashboard/layout.tsx`

## License

Proprietary - LORENZ SaaS Platform
