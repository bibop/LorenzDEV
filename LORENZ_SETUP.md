# 🤖 LORENZ - Super AI Bot Setup

**Data**: 7 Gennaio 2026
**Status**: Pronto per deployment

---

## 📋 Cosa fa LORENZ

LORENZ è il tuo assistente AI personale che gestisce tutto via Telegram:

✅ **Email Intelligence** - Controlla, legge e risponde alle email
✅ **Server Management** - Esegui comandi e controlla il server
✅ **AI Chat** - Chatta con Claude AI per risolvere problemi
✅ **Monitoring Centralizzato** - Tutti gli alert in un posto solo

---

## 🚀 STEP 1: Crea il Bot Telegram

1. Apri Telegram e cerca **@BotFather**
2. Invia `/newbot`
3. **Nome**: `LORENZ`
4. **Username**: `lorenz_bibop_bot` (o simile, deve finire con `_bot`)
5. **Salva il TOKEN** che ricevi (es. `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

## 🛠️ STEP 2: Deploy sul Server

Esegui questi comandi sul server:

```bash
# SSH nel server
ssh linuxuser@80.240.31.197

# Crea directory
sudo mkdir -p /opt/lorenz-bot
sudo chown linuxuser:linuxuser /opt/lorenz-bot
cd /opt/lorenz-bot

# Carica i file (dal tuo PC locale)
# Poi sul server:

# Installa dipendenze Python
pip3 install -r lorenz-requirements.txt

# Configura il token (sostituisci YOUR_BOT_TOKEN_HERE con il token di BotFather)
sudo nano lorenz-bot.service
# Cambia: Environment=TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
#     con: Environment=TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Installa servizio systemd
sudo cp lorenz-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lorenz-bot
sudo systemctl start lorenz-bot

# Verifica status
sudo systemctl status lorenz-bot
```

---

## ✅ STEP 3: Test il Bot

1. Apri Telegram
2. Cerca `@lorenz_bibop_bot` (o il nome che hai scelto)
3. Invia `/start`

Dovresti ricevere il messaggio di benvenuto!

---

## 📱 Comandi Disponibili

### Email
- `/email` - Controlla nuove email
- `/email_read <id>` - Leggi email specifica
- `/email_reply <id> <testo>` - Rispondi

### Server
- `/status` - Status server
- `/logs <servizio>` - Mostra logs
- `/exec <comando>` - Esegui comando sicuro

### AI
- `/ask <domanda>` - Chiedi a Claude AI
- Oppure scrivi direttamente una domanda!

### Monitoring
- `/health` - Health check completo

---

## 🔐 Configurazione Opzionale: Claude API

Per abilitare l'AI intelligence completa:

1. **Ottieni API Key**: https://console.anthropic.com
2. **Configura nel service**:
```bash
sudo nano /etc/systemd/system/lorenz-bot.service
# Aggiungi: Environment=CLAUDE_API_KEY=sk-ant-xxx
sudo systemctl daemon-reload
sudo systemctl restart lorenz-bot
```

---

## 📊 Integrazione Monitoring

LORENZ può ricevere alert da:
- Guardian Bot
- Netdata
- Healthchecks.io

**Per configurare**, modifica i sistemi di monitoring per inviare notifiche a LORENZ invece che direttamente a te.

---

## 🛠️ Comandi Utili

```bash
# Logs in real-time
sudo tail -f /var/log/lorenz-bot.log

# Restart bot
sudo systemctl restart lorenz-bot

# Stop bot
sudo systemctl stop lorenz-bot

# Status
sudo systemctl status lorenz-bot
```

---

## 🎯 Prossimi Passi

Una volta attivo, puoi:

1. **Testare email**: `/email`
2. **Controllare server**: `/status`
3. **Fare domande AI**: "Perché il server è lento?"
4. **Eseguire comandi**: `/exec uptime`

---

## 💡 Tips

- LORENZ risponde solo al tuo Chat ID (1377101484)
- Per sicurezza, comandi pericolosi sono bloccati
- Claude AI è opzionale ma consigliato
- Puoi chattare normalmente - se fai domande, risponde con AI

---

## 🆘 Troubleshooting

**Bot non risponde?**
```bash
sudo systemctl status lorenz-bot
sudo journalctl -u lorenz-bot -n 50
```

**Errore permessi?**
```bash
sudo chown -R linuxuser:linuxuser /opt/lorenz-bot
sudo chmod +x /opt/lorenz-bot/lorenz-bot.py
```

**Dipendenze mancanti?**
```bash
pip3 install --upgrade -r lorenz-requirements.txt
```

---

**Creato da**: Claude Code
**Data**: 2026-01-07
