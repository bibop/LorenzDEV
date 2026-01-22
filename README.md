# 🤖 LORENZ - Super AI Assistant

**LORENZ** è un assistente AI personale centralizzato che gestisce email, server, e comunicazioni via Telegram.

---

## 📋 Funzionalità Principali

### ✅ Email Intelligence
- Gestione multi-account email (IMAP/SMTP)
- Lettura, risposta e categorizzazione automatica
- Integrazione con Claude AI per risposte intelligenti
- Tracking email in Supabase database

### ✅ Server Management
- Esecuzione comandi SSH sicuri
- Monitoring servizi systemd
- Lettura logs in real-time
- Health check automatici

### ✅ AI Chat con Claude
- Conversazioni intelligenti via Telegram
- Context-aware responses
- Storico conversazioni in database
- Multi-provider support (Claude, OpenAI, Gemini)

### ✅ Web Interface
- Dashboard integrata nel sito Bibop.com
- Visualizzazione statistiche email
- Gestione conversazioni
- Settings e configurazione

### ✅ Monitoring Centralizzato
- Alert da Guardian Bot
- Notifiche Netdata
- Healthchecks.io integration
- Sistema di alert unificato

---

## 🏗️ Architettura

```
LORENZ/
├── lorenz-bot.py              # Bot Telegram principale (40KB)
├── lorenz-api.py              # API server per web interface (10KB)
├── lorenz-bot.service         # Systemd service per bot
├── lorenz-api.service         # Systemd service per API
├── lorenz-requirements.txt    # Dipendenze Python per bot
├── lorenz-api-requirements.txt # Dipendenze Python per API
└── docs/
    ├── LORENZ_SETUP.md                    # Setup completo
    ├── LORENZ_EMAIL_CREDENTIALS.md        # Gestione email
    ├── LORENZ_MULTI_ACCOUNT_UPDATE.md     # Multi-account setup
    ├── LORENZ_WEB_INTERFACE_SETUP.md      # Web dashboard
    ├── LORENZ_RAG_SYSTEM.md               # RAG per knowledge base
    ├── LORENZ_SECURITY_MODELS.md          # Security patterns
    └── LORENZ_SUPER_AI_ASSISTANT.md       # Roadmap completa
```

**Web Interface** (nel repo Bibop Website):
```
bibop-site/
├── src/app/[locale]/lorenz/           # Next.js pages
│   ├── page.tsx                       # Dashboard principale
│   └── system/page.tsx                # System status
├── src/app/api/lorenz/                # API routes
│   └── status/route.ts                # Status endpoint
├── src/components/
│   ├── lorenz-dashboard.tsx           # Dashboard component
│   ├── lorenz-chat.tsx                # Chat interface
│   └── lorenz-settings.tsx            # Settings panel
└── src/lib/
    ├── supabase.ts                    # Database helpers
    └── lorenz-providers.ts            # AI provider config
```

---

## 🚀 Quick Start

### 1. Installazione Dipendenze

```bash
# Bot Telegram
pip3 install -r lorenz-requirements.txt

# API Server (opzionale se usi la web interface)
pip3 install -r lorenz-api-requirements.txt
```

### 2. Configurazione Bot Telegram

1. Crea bot con [@BotFather](https://t.me/BotFather)
2. Ottieni il token
3. Configura variabili d'ambiente:

```bash
export TELEGRAM_BOT_TOKEN="your-token-here"
export TELEGRAM_CHAT_ID="1377101484"  # Il tuo chat ID
export CLAUDE_API_KEY="sk-ant-xxx"    # Opzionale ma consigliato
```

### 3. Configurazione Email (Opzionale)

```bash
# Account principale
export SMTP_HOST="mail.hyperloopitalia.com"
export SMTP_PORT="587"
export SMTP_USER="info@bibop.com"
export SMTP_PASS="your-password"

export IMAP_HOST="mail.hyperloopitalia.com"
export IMAP_PORT="993"
export IMAP_USER="info@bibop.com"
export IMAP_PASS="your-password"

# Supabase per tracking
export NEXT_PUBLIC_SUPABASE_URL="https://xxxxx.supabase.co"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="xxxxx"
export SUPABASE_SERVICE_ROLE_KEY="xxxxx"
```

### 4. Avvio Manuale (Testing)

```bash
# Avvia bot
python3 lorenz-bot.py

# Avvia API server (opzionale)
python3 lorenz-api.py
```

### 5. Deploy Produzione (Systemd)

```bash
# Copia service files
sudo cp lorenz-bot.service /etc/systemd/system/
sudo cp lorenz-api.service /etc/systemd/system/

# Edita i file per configurare le variabili d'ambiente
sudo nano /etc/systemd/system/lorenz-bot.service
sudo nano /etc/systemd/system/lorenz-api.service

# Abilita e avvia servizi
sudo systemctl daemon-reload
sudo systemctl enable lorenz-bot lorenz-api
sudo systemctl start lorenz-bot lorenz-api

# Verifica status
sudo systemctl status lorenz-bot
sudo systemctl status lorenz-api
```

---

## 📱 Comandi Telegram

### Email Management
- `/email` - Controlla nuove email
- `/email_list` - Lista email recenti
- `/email_read <id>` - Leggi email specifica
- `/email_reply <id> <messaggio>` - Rispondi a email
- `/email_stats` - Statistiche email

### Server Management
- `/status` - Status generale server
- `/logs <service>` - Mostra logs servizio
- `/exec <comando>` - Esegui comando sicuro (whitelist)
- `/services` - Lista servizi attivi

### AI Assistant
- `/ask <domanda>` - Chiedi a Claude AI
- `/chat` - Modalità conversazione
- Scrivi direttamente una domanda per risposta AI

### System
- `/health` - Health check completo
- `/help` - Mostra tutti i comandi
- `/settings` - Configurazione bot

---

## 🗄️ Database Schema (Supabase)

### Tabelle Principali

**conversations** - Storico conversazioni
```sql
- id (uuid)
- chat_id (bigint)
- timestamp (timestamp)
- user_message (text)
- bot_response (text)
- message_type (text)
- context (jsonb)
```

**user_preferences** - Impostazioni utente
```sql
- id (uuid)
- chat_id (bigint)
- preferred_email (text)
- notification_settings (jsonb)
- ai_personality (text)
- language (text)
```

**email_tracking** - Tracking email
```sql
- id (uuid)
- chat_id (bigint)
- email_account (text)
- subject (text)
- sender (text)
- action (text)
- metadata (jsonb)
```

**command_logs** - Log comandi eseguiti
```sql
- id (uuid)
- chat_id (bigint)
- command (text)
- parameters (jsonb)
- status (text)
- execution_time_ms (integer)
```

**ai_interactions** - Tracking AI usage
```sql
- id (uuid)
- chat_id (bigint)
- prompt (text)
- response (text)
- model (text)
- tokens_used (integer)
- cost_usd (numeric)
```

Schema completo in `bibop-site/supabase-schema.sql`

---

## 🔐 Sicurezza

### Comandi Whitelisted
Solo comandi sicuri sono permessi via `/exec`:
- `uptime`, `free -h`, `df -h`
- `systemctl status <service>`
- `journalctl -u <service> -n 50`
- `ps aux | grep <process>`

### Autenticazione
- Solo il tuo `TELEGRAM_CHAT_ID` può usare il bot
- Token Telegram in variabili d'ambiente
- API keys in systemd environment file

### Email Credentials
- Password criptate in environment
- Nessuna password in codice
- TLS/SSL per tutte le connessioni

---

## 📊 Monitoring

### Logs
```bash
# Bot logs
sudo journalctl -u lorenz-bot -f

# API logs
sudo journalctl -u lorenz-api -f

# Logs entrambi
sudo journalctl -u lorenz-* -f
```

### Health Checks
- Endpoint: `http://localhost:5001/health`
- Telegram: `/health`
- Web dashboard: `https://bibop.com/en/lorenz/system`

---

## 🛠️ Sviluppo

### Testing Locale
```bash
# Avvia bot in modalità debug
TELEGRAM_BOT_TOKEN="xxx" python3 lorenz-bot.py

# Test API
curl http://localhost:5001/health
curl http://localhost:5001/api/lorenz/status
```

### Aggiungere Nuovi Comandi
Modifica `lorenz-bot.py`:
```python
async def nuovo_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per nuovo comando"""
    await update.message.reply_text("Risposta comando")

# Registra handler in main()
app.add_handler(CommandHandler("nuovo", nuovo_comando))
```

---

## 🌐 Web Interface

La web interface è integrata nel sito Bibop.com:

**URL**: https://bibop.com/en/lorenz

**Features**:
- Dashboard conversazioni
- Statistiche email
- System status
- Settings pannello
- Chat interface (coming soon)

**Tech Stack**:
- Next.js 15 + React 19
- Tailwind CSS
- Supabase per database
- Real-time updates

---

## 📈 Roadmap

### ✅ Completato
- [x] Bot Telegram base
- [x] Email intelligence multi-account
- [x] Server management
- [x] Claude AI integration
- [x] Supabase database
- [x] Web dashboard
- [x] Systemd services

### 🚧 In Sviluppo
- [ ] RAG system per knowledge base personale
- [ ] Calendar integration (Google Calendar)
- [ ] Proactive notifications
- [ ] Voice messages support
- [ ] Mobile app (React Native)

### 🔮 Futuro
- [ ] Multi-user support
- [ ] Plugin system
- [ ] Custom workflows automation
- [ ] Advanced analytics
- [ ] Self-learning capabilities

Vedi `LORENZ_SUPER_AI_ASSISTANT.md` per roadmap completa.

---

## 📝 Documentazione

- **Setup Completo**: `LORENZ_SETUP.md`
- **Email Management**: `LORENZ_EMAIL_CREDENTIALS.md`
- **Web Interface**: `LORENZ_WEB_INTERFACE_SETUP.md`
- **RAG System**: `LORENZ_RAG_SYSTEM.md`
- **Security**: `LORENZ_SECURITY_MODELS.md`
- **Roadmap**: `LORENZ_SUPER_AI_ASSISTANT.md`

---

## 🐛 Troubleshooting

### Bot non risponde
```bash
sudo systemctl status lorenz-bot
sudo journalctl -u lorenz-bot -n 100
```

### Errori email
- Verifica credenziali IMAP/SMTP
- Controlla TLS/SSL settings
- Testa connessione manualmente

### Database issues
- Verifica Supabase URL e keys
- Controlla schema tabelle
- Verifica RLS policies

---

## 👤 Autore

**Bibop Gresta** - Hyperloop co-founder, Tech Entrepreneur
- Website: https://bibop.com
- Telegram: @bibopgresta

---

## 📄 License

Private project - All rights reserved

---

**Versione**: 2.0
**Ultimo aggiornamento**: 12 Gennaio 2026
**Status**: Production Ready ✅
