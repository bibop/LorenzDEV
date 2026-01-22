# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LORENZ** is a Telegram-based AI personal assistant for Bibop Gresta that manages:
- Multi-account email (8 accounts via IMAP/SMTP)
- Server commands via local subprocess (runs on server 80.240.31.197)
- AI conversations with Claude API (Haiku/Sonnet routing)
- Memory/context via SQLite + optional Qdrant RAG

Production: Bot and API run as systemd services on the same server.

## Essential Commands

```bash
# Install dependencies
pip3 install -r lorenz-requirements.txt      # Bot
pip3 install -r lorenz-api-requirements.txt  # API
pip3 install -r lorenz-rag-requirements.txt  # RAG (optional)

# Run locally (set env vars first)
python3 lorenz-bot.py    # Telegram bot
python3 lorenz-api.py    # REST API on port 5001

# Production (systemd)
sudo systemctl start lorenz-bot lorenz-api
sudo journalctl -u lorenz-bot -f  # View logs
```

## Architecture

### Core Components

```
lorenz-bot.py (1500 lines)
├── EmailManager       - Multi-account IMAP/SMTP with signatures
├── ServerCommander    - Local subprocess execution
├── ClaudeAI           - API with Haiku/Sonnet auto-routing
├── MemoryManager      - SQLite-based conversation storage
└── Telegram handlers  - Command handlers (/email, /ask, /status, etc.)

lorenz-api.py
└── Flask REST API for web dashboard (status, stats, conversations)

lorenz_rag_system.py (optional)
└── LorenzRAG - Hybrid search with Qdrant + BM25 + reranking
```

### Data Flow

1. **Telegram message** → Authorization check (`AUTHORIZED_CHAT_ID`)
2. **Command routing** → Specific handler or AI fallback
3. **AI queries** → Context built from MemoryManager/RAG → Claude API
4. **Responses** → Stored in SQLite, sent back via Telegram

### Memory System

Two modes (auto-detected):
- **Basic**: SQLite-only (`MemoryManager` class) - stores conversations, preferences, usage stats
- **Advanced RAG**: Qdrant vector DB + BM25 + reranking (`LorenzRAG` class)

RAG availability is checked at startup; falls back to basic if unavailable.

## Key Implementation Details

### Email Accounts

Configured in `EMAIL_ACCOUNTS` dict. Each account has:
- IMAP/SMTP host, port, credentials
- Custom signature from `EMAIL_SIGNATURES` dict

Active accounts: info, bibop, hyperloop, gmail, outlook, wdfholding, norma, lorenz

### AI Model Routing

`ClaudeAI.ask()` auto-routes queries:
- **Haiku**: Simple/short queries (cost-effective)
- **Sonnet**: Complex/analytical queries

Routing logic in `QueryRouter.route()` when RAG is available.

### Authorization

Single-user bot. Only `AUTHORIZED_CHAT_ID` (default: 1377101484) can interact:
```python
def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == AUTHORIZED_CHAT_ID
```

### Safe Command Execution

`/exec` command only allows whitelisted commands:
```python
safe_commands = ['ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free', 'ps']
```

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `AUTHORIZED_CHAT_ID` - Your Telegram chat ID (default: 1377101484)

Optional:
- `CLAUDE_API_KEY` - For AI responses
- `MEMORY_DB_PATH` - SQLite path (default: `/opt/lorenz-bot/lorenz_memory.db`)
- `QDRANT_HOST`, `QDRANT_PORT` - For RAG system
- `EMAIL_*_PASSWORD` - Per-account email passwords (some have hardcoded defaults)

## Adding New Features

### New Telegram Command

1. Create async handler in `lorenz-bot.py`:
```python
async def cmd_newfeature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    # Your logic
    await update.message.reply_text("Response")
```

2. Register in `main()`:
```python
app.add_handler(CommandHandler("newfeature", cmd_newfeature))
```

3. Add to help text in `start()` function

### New API Endpoint

Add to `lorenz-api.py`:
```python
@app.route('/api/endpoint', methods=['GET'])
def endpoint():
    return jsonify({'data': 'value'})
```

### New Email Account

Add entry to `EMAIL_ACCOUNTS` dict with IMAP/SMTP configuration.

## Related Projects

Web interface is in separate repo: `/Users/bibop/Documents/AI/Bibop Website/bibop-site`
- Dashboard: `src/app/[locale]/lorenz/page.tsx`
- API routes: `src/app/api/lorenz/`

## Documentation

- `LORENZ_SETUP.md` - Full setup guide
- `LORENZ_EMAIL_CREDENTIALS.md` - Email configuration
- `LORENZ_RAG_SYSTEM.md` - RAG architecture details
- `LORENZ_SUPER_AI_ASSISTANT.md` - Full roadmap
- `MAIL_AUTODISCOVER_SETUP.md` - **Procedura enterprise per nuovi domini email**

## Mail Server Configuration (Vultr 80.240.31.197)

**IMPORTANTE**: Quando si aggiunge un nuovo dominio email, seguire SEMPRE la procedura in `MAIL_AUTODISCOVER_SETUP.md`.

Server mail: `mail.hyperloopitalia.com`
- IMAP: 993 (SSL)
- SMTP: 587 (STARTTLS)

Domini configurati: bibop.com, hyper.works, hyperloopitalia.com, hyperlabai.com, hyperloop.ventures, wdfholding.com, hyper-works.com

Per ogni nuovo dominio servono questi record DNS:
```
autodiscover    A     80.240.31.197
autoconfig      A     80.240.31.197
@               MX    10 mail.hyperloopitalia.com.
@               TXT   "v=spf1 mx a:mail.hyperloopitalia.com ~all"
```

## Output Directory Convention

**IMPORTANT**: All generated output files that are NOT related to LORENZ development should be saved to:

```
/Users/bibop/Documents/AI/Lorenz/output/
```

This includes:
- Preventivi e proposte commerciali
- Documenti per clienti
- Report e analisi
- Qualsiasi altro file generato su richiesta

The `output/` folder keeps business/external documents separate from the codebase.
