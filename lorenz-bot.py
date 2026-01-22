#!/usr/bin/env python3
"""
🤖 LORENZ - Super Bot Telegram Centralizzato
===========================================================

Funzionalità:
- 📧 Gestione email intelligente (IMAP/SMTP)
- 💻 Comandi server via SSH
- 🧠 AI integration con Claude
- 📊 Monitoring alerts centralizzati
- 🔐 Autenticazione sicura

Autore: Claude Code
Data: 2026-01-07
"""

import os
import sys
import time
import json
import logging
import asyncio
import imaplib
import email
import smtplib
import subprocess
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# HTTP Client per Claude API
import aiohttp

# RAG System (Advanced)
try:
    from lorenz_rag_system import LorenzRAG, QueryRouter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("⚠️ RAG System not available, using basic memory")

# Skills System v2.0 (GOD + Emergent Skills + MNEME)
try:
    from lorenz_skills import (
        SkillsManager, SkillRouter, SkillType, SkillResult,
        MNEME, get_skills_manager, get_mneme
    )
    SKILLS_AVAILABLE = True
except ImportError:
    SKILLS_AVAILABLE = False
    logging.warning("⚠️ Skills System not available")

# AI Orchestrator (Multi-model routing)
try:
    from lorenz_ai_orchestrator import AIOrchestrator, TaskType
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    logging.warning("⚠️ AI Orchestrator not available")

# Secrets Manager (secure credential storage)
try:
    from lorenz_secrets import SecretsManager
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False
    logging.warning("⚠️ Secrets Manager not available")

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

# Telegram Bot Token (sostituire con il nuovo bot)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_NEW_BOT_TOKEN_HERE')
AUTHORIZED_CHAT_ID = int(os.getenv('AUTHORIZED_CHAT_ID', '1377101484'))

# Multi-Account Email Configuration
EMAIL_ACCOUNTS = {
    'info': {
        'email': 'info@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': 'infOB1b0p2026Ai@',
        'name': '📧 Info Bibop',
        'display_name': 'Bibop Info'
    },
    'bibop': {
        'email': 'bibop@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_BIBOP_PASSWORD', 'bibOb1b0P2026Ab@'),
        'name': '👤 Bibop Personal',
        'display_name': 'Bibop Gresta'
    },
    'hyperloop': {
        'email': 'bibop@hyperloopitalia.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_HYPERLOOP_PASSWORD', ''),
        'name': '🚄 Hyperloop Italia'
    },
    'gmail': {
        'email': 'mrbibop@gmail.com',
        'imap_host': 'imap.gmail.com',
        'smtp_host': 'smtp.gmail.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_GMAIL_APP_PASSWORD', ''),  # Requires App Password
        'name': '📮 Gmail Personal'
    },
    'outlook': {
        'email': 'bibophome@outlook.com',
        'imap_host': 'outlook.office365.com',
        'smtp_host': 'smtp.office365.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_OUTLOOK_PASSWORD', ''),
        'name': '📨 Outlook Personal'
    },
    'wdfholding': {
        'email': 'bibop@wdfholding.com',
        'imap_host': os.getenv('EMAIL_WDF_IMAP_HOST', 'mail.wdfholding.com'),
        'smtp_host': os.getenv('EMAIL_WDF_SMTP_HOST', 'mail.wdfholding.com'),
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_WDF_PASSWORD', ''),
        'name': '🏢 WDF Holding'
    },
    'norma': {
        'email': 'norma@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_NORMA_PASSWORD', 'N0rm@B1b0p2025!'),
        'name': '👩 Norma Assistant',
        'display_name': 'Norma Assistant'
    },
    'lorenz': {
        'email': 'lorenz@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_LORENZ_PASSWORD', 'lorEb1b0P2026Al@'),
        'name': '🤖 Lorenz AI Assistant',
        'display_name': 'Lorenz Visconti Ferri'
    }
    # TODO: Aggiungere lorenz@hyper.works dopo migrazione da GoDaddy a Vultr/Postfix
    # 'lorenz_hyperworks': {
    #     'email': 'lorenz@hyper.works',
    #     'imap_host': 'mail.hyper.works',
    #     'smtp_host': 'mail.hyper.works',
    #     'imap_port': 993,
    #     'smtp_port': 587,
    #     'password': os.getenv('EMAIL_LORENZ_HYPERWORKS_PASSWORD', ''),
    #     'name': '🚀 Lorenz Hyper.works'
    # }
}

# Default account
DEFAULT_EMAIL_ACCOUNT = 'info'

# Email Signatures Configuration
EMAIL_SIGNATURES = {
    'lorenz': """

--
(former Hyperloop Italia)

Lorenz Visconti
Chief Executive Team
Of the Founder & CEO
lorenz@bibop.com
https://www.bibop.com
Hyperloop: The Bestselling Book! Do you want to know more? Click here!

CONFIDENTIALITY NOTICE: The information contained in this email message and any attachments may be confidential and privileged, and exempt from disclosure under applicable law. This email is intended only for the exclusive use of the person or entity to whom it is addressed. If you are not the intended recipient, please be aware that any use, distribution or copying of this communication is strictly prohibited. If you have received this communication in error, please notify the sender immediately by return email or by telephone and delete or destroy this email message and any attachments to it. Thank you.
""",
    'lorenz_hyperworks': """

--
(former Hyperloop Italia)

Lorenz Visconti
Chief Executive Team
Of the Founder & CEO
lorenz@hyper.works
https://www.hyper.works
Hyperloop: The Bestselling Book! Do you want to know more? Click here!

CONFIDENTIALITY NOTICE: The information contained in this email message and any attachments may be confidential and privileged, and exempt from disclosure under applicable law. This email is intended only for the exclusive use of the person or entity to whom it is addressed. If you are not the intended recipient, please be aware that any use, distribution or copying of this communication is strictly prohibited. If you have received this communication in error, please notify the sender immediately by return email or by telephone and delete or destroy this email message and any attachments to it. Thank you.
""",
    'norma': """

--
Norma
Executive Assistant to Bibop Gresta
📧 norma@bibop.com
📱 Available via Telegram

🌐 bibop.com
""",
    'default': """

--
Sent via LORENZ Bot
📧 Automated Email System
"""
}

# Server SSH Configuration
SSH_HOST = '80.240.31.197'
SSH_USER = 'linuxuser'
SSH_KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

# Claude API (opzionale - richiede chiave API)
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'

# Memory/RAG System Configuration
MEMORY_DB_PATH = os.getenv('MEMORY_DB_PATH', '/opt/lorenz-bot/lorenz_memory.db')
MEMORY_CONTEXT_LIMIT = 10  # Number of recent messages to include in context
MEMORY_SEARCH_LIMIT = 5    # Number of relevant past messages to retrieve

# Qdrant Configuration (for RAG)
QDRANT_HOST = os.getenv('QDRANT_HOST', 'mail.hyperloopitalia.com')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6335'))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# MEMORY/RAG SYSTEM
# ============================================================================

class MemoryManager:
    """
    Retrieval-Augmented Generation (RAG) System for LORENZ

    Funzionalità:
    - Memorizza tutte le conversazioni in SQLite
    - Recupera contesto rilevante per query
    - Apprende preferenze utente
    - Fornisce insights su pattern di utilizzo
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Inizializza il database SQLite con schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Tabella conversazioni
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT,
                    bot_response TEXT,
                    message_type TEXT,
                    context_data TEXT,
                    sentiment TEXT
                )
            ''')

            # Tabella preferenze utente
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key TEXT UNIQUE,
                    preference_value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabella statistiche utilizzo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_date DATE,
                    command_type TEXT,
                    count INTEGER DEFAULT 1,
                    UNIQUE(stat_date, command_type)
                )
            ''')

            # Indici per performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_type ON conversations(message_type)')

            conn.commit()
            conn.close()
            logger.info(f"✅ Memory database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Error initializing memory database: {e}")

    def store_conversation(self, user_message: str, bot_response: str,
                         message_type: str = 'general', context_data: Dict = None):
        """Memorizza una conversazione nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            context_json = json.dumps(context_data) if context_data else None

            cursor.execute('''
                INSERT INTO conversations
                (user_message, bot_response, message_type, context_data)
                VALUES (?, ?, ?, ?)
            ''', (user_message, bot_response, message_type, context_json))

            conn.commit()
            conn.close()
            logger.debug(f"Stored conversation: {message_type}")
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")

    def get_recent_context(self, limit: int = 10) -> List[Dict]:
        """Recupera le conversazioni più recenti"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, user_message, bot_response, message_type
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            results = cursor.fetchall()
            conn.close()

            conversations = []
            for row in reversed(results):  # Ordine cronologico
                conversations.append({
                    'timestamp': row[0],
                    'user': row[1],
                    'bot': row[2],
                    'type': row[3]
                })

            return conversations
        except Exception as e:
            logger.error(f"Error getting recent context: {e}")
            return []

    def search_relevant_context(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Cerca conversazioni rilevanti basate su keyword matching
        (In futuro: vector embeddings per semantic search)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Simple keyword search (migliorabile con embeddings)
            keywords = query.lower().split()[:5]  # Top 5 keywords

            # Build LIKE query for each keyword
            like_conditions = ' OR '.join(['user_message LIKE ?' for _ in keywords])
            like_params = [f'%{kw}%' for kw in keywords]

            cursor.execute(f'''
                SELECT timestamp, user_message, bot_response, message_type
                FROM conversations
                WHERE {like_conditions}
                ORDER BY timestamp DESC
                LIMIT ?
            ''', like_params + [limit])

            results = cursor.fetchall()
            conn.close()

            relevant = []
            for row in results:
                relevant.append({
                    'timestamp': row[0],
                    'user': row[1],
                    'bot': row[2],
                    'type': row[3]
                })

            return relevant
        except Exception as e:
            logger.error(f"Error searching relevant context: {e}")
            return []

    def learn_preference(self, key: str, value: str):
        """Memorizza una preferenza utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (preference_key, preference_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))

            conn.commit()
            conn.close()
            logger.info(f"Learned preference: {key} = {value}")
        except Exception as e:
            logger.error(f"Error learning preference: {e}")

    def get_preference(self, key: str) -> Optional[str]:
        """Recupera una preferenza utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT preference_value FROM user_preferences
                WHERE preference_key = ?
            ''', (key,))

            result = cursor.fetchone()
            conn.close()

            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return None

    def track_command_usage(self, command_type: str):
        """Traccia l'utilizzo dei comandi per analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.now().date()

            cursor.execute('''
                INSERT INTO usage_stats (stat_date, command_type, count)
                VALUES (?, ?, 1)
                ON CONFLICT(stat_date, command_type)
                DO UPDATE SET count = count + 1
            ''', (today, command_type))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")

    def get_usage_stats(self, days: int = 7) -> Dict:
        """Ottiene statistiche di utilizzo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).date()

            cursor.execute('''
                SELECT command_type, SUM(count) as total
                FROM usage_stats
                WHERE stat_date >= ?
                GROUP BY command_type
                ORDER BY total DESC
            ''', (cutoff_date,))

            results = cursor.fetchall()
            conn.close()

            stats = {row[0]: row[1] for row in results}
            return stats
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}

    def get_user_profile(self) -> Dict:
        """Genera un profilo utente basato sulla memoria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_conversations = cursor.fetchone()[0]

            # Most used command types
            cursor.execute('''
                SELECT message_type, COUNT(*) as count
                FROM conversations
                GROUP BY message_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            top_activities = cursor.fetchall()

            # First and last interaction
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM conversations')
            first_last = cursor.fetchone()

            # Recent preferences
            cursor.execute('''
                SELECT preference_key, preference_value
                FROM user_preferences
                ORDER BY updated_at DESC
                LIMIT 10
            ''')
            preferences = cursor.fetchall()

            conn.close()

            return {
                'total_conversations': total_conversations,
                'top_activities': [(act[0], act[1]) for act in top_activities],
                'first_interaction': first_last[0],
                'last_interaction': first_last[1],
                'preferences': {pref[0]: pref[1] for pref in preferences}
            }
        except Exception as e:
            logger.error(f"Error generating user profile: {e}")
            return {}

    def build_context_for_claude(self, query: str) -> str:
        """
        Costruisce un contesto intelligente per Claude AI
        combinando conversazioni recenti e rilevanti
        """
        context_parts = []

        # Recent conversations
        recent = self.get_recent_context(limit=MEMORY_CONTEXT_LIMIT)
        if recent:
            context_parts.append("Recent Conversation History:")
            for conv in recent[-5:]:  # Last 5
                context_parts.append(f"User: {conv['user']}")
                context_parts.append(f"Assistant: {conv['bot'][:200]}")  # Truncate long responses
            context_parts.append("")

        # Relevant past conversations
        relevant = self.search_relevant_context(query, limit=MEMORY_SEARCH_LIMIT)
        if relevant:
            context_parts.append("Relevant Past Conversations:")
            for conv in relevant[:3]:  # Top 3 relevant
                context_parts.append(f"- User asked: {conv['user']}")
                context_parts.append(f"  I responded: {conv['bot'][:150]}")
            context_parts.append("")

        # User preferences
        profile = self.get_user_profile()
        if profile.get('preferences'):
            context_parts.append("User Preferences:")
            for key, value in list(profile['preferences'].items())[:5]:
                context_parts.append(f"- {key}: {value}")
            context_parts.append("")

        return "\n".join(context_parts)

# ============================================================================
# EMAIL MANAGER
# ============================================================================

class EmailManager:
    """Gestione intelligente multi-account delle email"""

    def __init__(self, accounts_config):
        self.accounts = accounts_config
        self.current_account = DEFAULT_EMAIL_ACCOUNT

    def set_account(self, account_key: str) -> bool:
        """Imposta l'account corrente"""
        if account_key in self.accounts:
            self.current_account = account_key
            return True
        return False

    def get_account_info(self, account_key: str = None) -> Dict:
        """Ottiene info account"""
        key = account_key or self.current_account
        return self.accounts.get(key, {})

    def list_accounts(self) -> List[Dict]:
        """Lista tutti gli account configurati"""
        accounts_list = []
        for key, config in self.accounts.items():
            has_password = bool(config.get('password'))
            accounts_list.append({
                'key': key,
                'name': config.get('name', 'Unknown'),
                'email': config.get('email', ''),
                'configured': has_password
            })
        return accounts_list

    def connect_imap(self, account_key: str = None):
        """Connessione IMAP per account specifico"""
        account = self.get_account_info(account_key)
        if not account or not account.get('password'):
            logger.error(f"Account {account_key or self.current_account} non configurato")
            return None

        try:
            mail = imaplib.IMAP4_SSL(account['imap_host'], account['imap_port'])
            mail.login(account['email'], account['password'])
            return mail
        except Exception as e:
            logger.error(f"IMAP connection error for {account.get('email')}: {e}")
            return None

    def get_unread_emails(self, limit=10, account_key: str = None):
        """Recupera email non lette da account specifico"""
        account = self.get_account_info(account_key)
        try:
            mail = self.connect_imap(account_key)
            if not mail:
                return []

            mail.select('INBOX')
            _, message_numbers = mail.search(None, 'UNSEEN')

            emails = []
            for num in message_numbers[0].split()[-limit:]:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)

                emails.append({
                    'id': num.decode(),
                    'from': message.get('From', 'Unknown'),
                    'subject': message.get('Subject', 'No Subject'),
                    'date': message.get('Date', ''),
                    'body': self._get_email_body(message),
                    'account': account.get('email', '')
                })

            mail.close()
            mail.logout()
            return emails

        except Exception as e:
            logger.error(f"Error getting emails for {account.get('email')}: {e}")
            return []

    def get_all_unread_emails(self, limit=5):
        """Recupera email non lette da TUTTI gli account"""
        all_emails = []
        for account_key in self.accounts.keys():
            if self.accounts[account_key].get('password'):
                emails = self.get_unread_emails(limit=limit, account_key=account_key)
                all_emails.extend(emails)

        # Ordina per data (più recenti prima)
        # all_emails.sort(key=lambda x: x.get('date', ''), reverse=True)
        return all_emails

    def _get_email_body(self, message):
        """Estrae il corpo dell'email"""
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
        return body[:500]  # Primi 500 caratteri

    def send_email(self, to: str, subject: str, body: str, account_key: str = None, add_signature: bool = True):
        """Invia email dall'account specifico con firma automatica"""
        account = self.get_account_info(account_key)
        if not account or not account.get('password'):
            return False

        try:
            # Aggiungi firma se richiesta
            if add_signature:
                signature = EMAIL_SIGNATURES.get(account_key or self.current_account, EMAIL_SIGNATURES.get('default', ''))
                body = body + signature

            msg = MIMEMultipart()
            # Format From with display name: "Name" <email@domain.com>
            from email.utils import formataddr
            display_name = account.get('display_name', account.get('name', '').replace('📧 ', '').replace('👤 ', '').replace('🤖 ', '').replace('👩 ', '').replace('🚄 ', '').replace('📮 ', '').replace('📨 ', '').replace('🏢 ', ''))
            msg['From'] = formataddr((display_name, account['email']))
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(account['smtp_host'], account['smtp_port'])
            server.starttls()
            server.login(account['email'], account['password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Error sending email from {account.get('email')}: {e}")
            return False

    def mark_as_read(self, email_id: str, account_key: str = None):
        """Marca email come letta"""
        try:
            mail = self.connect_imap(account_key)
            if not mail:
                return False
            mail.select('INBOX')
            mail.store(email_id.encode(), '+FLAGS', '\\Seen')
            mail.close()
            mail.logout()
            return True
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False

    def search_emails(self, from_filter: str = None, subject_filter: str = None, limit=100, account_key: str = None):
        """Cerca email con filtri specifici"""
        account = self.get_account_info(account_key)
        try:
            mail = self.connect_imap(account_key)
            if not mail:
                return []

            mail.select('INBOX')

            # Costruisci query di ricerca IMAP
            search_criteria = []
            if from_filter:
                search_criteria.append(f'FROM "{from_filter}"')
            if subject_filter:
                search_criteria.append(f'SUBJECT "{subject_filter}"')

            search_query = ' '.join(search_criteria) if search_criteria else 'ALL'

            _, message_numbers = mail.search(None, search_query)

            emails = []
            for num in message_numbers[0].split()[:limit]:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)

                emails.append({
                    'id': num.decode(),
                    'from': message.get('From', 'Unknown'),
                    'subject': message.get('Subject', 'No Subject'),
                    'date': message.get('Date', ''),
                    'account': account.get('email', '')
                })

            mail.close()
            mail.logout()
            return emails

        except Exception as e:
            logger.error(f"Error searching emails in {account.get('email')}: {e}")
            return []

    def delete_emails(self, email_ids: List[str], account_key: str = None) -> int:
        """Cancella email specificate dagli ID (batch delete)"""
        account = self.get_account_info(account_key)
        deleted_count = 0

        try:
            mail = self.connect_imap(account_key)
            if not mail:
                return 0

            mail.select('INBOX')

            for email_id in email_ids:
                try:
                    # Marca come Deleted
                    mail.store(email_id.encode(), '+FLAGS', '\\Deleted')
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting email {email_id}: {e}")

            # Esegui expunge per rimuovere definitivamente
            mail.expunge()
            mail.close()
            mail.logout()

            logger.info(f"Deleted {deleted_count} emails from {account.get('email')}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error in batch delete for {account.get('email')}: {e}")
            return deleted_count

    def search_and_delete(self, from_filter: str = None, subject_filter: str = None, account_key: str = None) -> int:
        """Cerca e cancella email in base ai filtri"""
        emails = self.search_emails(from_filter=from_filter, subject_filter=subject_filter, account_key=account_key)
        if not emails:
            return 0

        email_ids = [email['id'] for email in emails]
        return self.delete_emails(email_ids, account_key=account_key)

# ============================================================================
# SERVER COMMANDER
# ============================================================================

class ServerCommander:
    """Esecuzione comandi server via SSH"""

    def __init__(self):
        self.host = SSH_HOST
        self.user = SSH_USER
        self.key_path = SSH_KEY_PATH

    def execute_command(self, command: str, timeout=30):
        """Esegue comando locale (il bot gira sul server)"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timeout after {timeout}s',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }

    def get_server_status(self):
        """Status generale server"""
        commands = {
            'uptime': 'uptime',
            'disk': 'df -h / | tail -1',
            'memory': "free -h | grep Mem | awk '{print $3\"/\"$2}'",
            'cpu': "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'",
            'services': 'sudo systemctl list-units --type=service --state=running | wc -l'
        }

        status = {}
        for key, cmd in commands.items():
            result = self.execute_command(cmd)
            status[key] = result['stdout'].strip() if result['success'] else 'Error'

        return status

# ============================================================================
# CLAUDE AI INTEGRATION
# ============================================================================

class ClaudeAI:
    """Integrazione con Claude API con routing intelligente Haiku/Sonnet"""

    # Model configuration
    MODELS = {
        'haiku': {
            'name': 'claude-3-5-haiku-20241022',
            'cost_input': 0.25,  # $ per 1M tokens
            'cost_output': 1.25,
            'max_tokens': 2048
        },
        'sonnet': {
            'name': 'claude-3-5-sonnet-20241022',
            'cost_input': 3.00,
            'cost_output': 15.00,
            'max_tokens': 4096
        }
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = CLAUDE_API_URL
        self.enabled = bool(api_key)
        self.stats = {'haiku_calls': 0, 'sonnet_calls': 0}

    async def ask(self, question: str, context: str = "", model: str = None) -> str:
        """
        Interroga Claude AI con routing intelligente

        Args:
            question: User question
            context: Optional context
            model: Force model ('haiku' or 'sonnet'), or None for auto-routing

        Returns:
            AI response
        """
        if not self.enabled:
            return "⚠️ Claude AI non configurato. Aggiungi CLAUDE_API_KEY."

        # Auto-route if no model specified
        if model is None and RAG_AVAILABLE:
            model = QueryRouter.route(question)
        elif model is None:
            model = 'haiku'  # Default to cheap model

        # Get model config
        model_config = self.MODELS.get(model, self.MODELS['haiku'])

        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            }

            messages = []
            if context:
                messages.append({
                    'role': 'user',
                    'content': f"Context:\n{context}\n\nQuestion: {question}"
                })
            else:
                messages.append({
                    'role': 'user',
                    'content': question
                })

            payload = {
                'model': model_config['name'],
                'max_tokens': model_config['max_tokens'],
                'messages': messages
            }

            # Track usage
            self.stats[f'{model}_calls'] = self.stats.get(f'{model}_calls', 0) + 1

            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data['content'][0]['text']

                        # Log model used
                        logger.info(f"🤖 Used {model.upper()} (call #{self.stats[f'{model}_calls']})")

                        return response
                    else:
                        error = await resp.text()
                        logger.error(f"Claude API error: {error}")
                        return f"❌ Error: {resp.status}"

        except Exception as e:
            logger.error(f"Claude AI error: {e}")
            return f"❌ Error: {str(e)}"

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            **self.stats,
            'total_calls': self.stats.get('haiku_calls', 0) + self.stats.get('sonnet_calls', 0)
        }

# ============================================================================
# TELEGRAM BOT HANDLERS
# ============================================================================

# Inizializza managers
email_manager = EmailManager(EMAIL_ACCOUNTS)
server_commander = ServerCommander()
claude_ai = ClaudeAI(CLAUDE_API_KEY)

# Initialize RAG or fallback to basic memory
if RAG_AVAILABLE:
    try:
        rag_system = LorenzRAG(
            db_path=MEMORY_DB_PATH.replace('.db', '_rag.db'),
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT
        )
        memory_manager = None  # Using RAG instead
        logger.info("✅ Advanced RAG System loaded")
    except Exception as e:
        logger.error(f"❌ RAG initialization failed: {e}, falling back to basic memory")
        rag_system = None
        memory_manager = MemoryManager(MEMORY_DB_PATH)
else:
    rag_system = None
    memory_manager = MemoryManager(MEMORY_DB_PATH)
    logger.info("ℹ️ Using basic memory system")

# Initialize Skills System v2.0
if SKILLS_AVAILABLE:
    try:
        skills_manager = get_skills_manager()
        skill_router = SkillRouter(skills_manager)
        logger.info(f"✅ Skills System loaded: {len(skills_manager.god_skills)} GOD, "
                   f"{len(skills_manager.emergent_skills)} Emergent")
    except Exception as e:
        logger.error(f"❌ Skills System initialization failed: {e}")
        skills_manager = None
        skill_router = None
else:
    skills_manager = None
    skill_router = None

# Initialize AI Orchestrator
if ORCHESTRATOR_AVAILABLE:
    try:
        ai_orchestrator = AIOrchestrator()
        logger.info("✅ AI Orchestrator loaded (multi-model routing)")
    except Exception as e:
        logger.error(f"❌ AI Orchestrator initialization failed: {e}")
        ai_orchestrator = None
else:
    ai_orchestrator = None

# Verifica autorizzazione
def is_authorized(update: Update) -> bool:
    """Verifica se l'utente è autorizzato"""
    return update.effective_chat.id == AUTHORIZED_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /start"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Non autorizzato")
        return

    welcome_msg = """
🤖 **LORENZ** - Attivo!

Comandi disponibili:

📧 **Email Multi-Account**
/email - Controlla email account corrente
/email_all - Controlla TUTTI gli account
/email_accounts - Lista account configurati
/email_switch <account> - Cambia account
/email_search <filtri> - Cerca email (from:/subject:)
/email_delete <filtri> - Cancella email in batch
/email_read <id> - Leggi email specifica
/email_reply <id> <testo> - Rispondi a email

💻 **Server**
/status - Status server
/logs <servizio> - Mostra logs
/restart <servizio> - Riavvia servizio
/exec <comando> - Esegui comando

🧠 **AI Assistant** (with Memory!)
/ask <domanda> - Chiedi a Claude AI
/analyze <cosa> - Analizza con AI

📊 **Monitoring**
/health - Health check completo
/alerts - Ultimi alert

🧬 **Memory & Learning**
/memory - Mostra statistiche memoria
/profile - Il tuo profilo utente
/forget <days> - Dimentica conversazioni vecchie

🎯 **Skills System v2.0**
/skills - Lista tutte le skills (GOD + Emergent)
/skill <name> [params] - Esegui skill specifica
/mneme - Knowledge Base stats & operations

🧠 **AI Orchestrator**
/orchestrator - Stats multi-model AI routing
/ai_test - Test rapido orchestrator

📚 **MNEME Commands**
/mneme search <query> - Cerca nella knowledge base
/mneme export - Esporta knowledge in JSON
/mneme add <title> | <content> - Aggiungi knowledge

🔧 **Utilità**
/help - Mostra questo messaggio

💡 Scrivi un messaggio per attivare una skill automaticamente!
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def cmd_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email - controlla account corrente"""
    if not is_authorized(update):
        return

    current_account = email_manager.current_account
    account_info = email_manager.get_account_info()

    await update.message.reply_text(f"📧 Controllo {account_info.get('name', 'email')}...")

    emails = email_manager.get_unread_emails(limit=5)

    if not emails:
        await update.message.reply_text(f"✅ Nessuna nuova email in {account_info.get('email', '')}")
        return

    msg = f"📬 **{len(emails)} nuove email** in {account_info.get('name', '')}:\n\n"
    for idx, email_data in enumerate(emails, 1):
        msg += f"{idx}. **Da:** {email_data['from'][:50]}\n"
        msg += f"   **Oggetto:** {email_data['subject'][:60]}\n"
        msg += f"   **ID:** `{email_data['id']}`\n\n"

    msg += "\nUsa `/email_read <id>` per leggere"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_email_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email_all - controlla tutti gli account"""
    if not is_authorized(update):
        return

    await update.message.reply_text("📧 Controllo TUTTI gli account email...")

    all_emails = email_manager.get_all_unread_emails(limit=5)

    if not all_emails:
        await update.message.reply_text("✅ Nessuna nuova email in tutti gli account")
        return

    # Raggruppa per account
    by_account = {}
    for email_data in all_emails:
        account_email = email_data.get('account', 'Unknown')
        if account_email not in by_account:
            by_account[account_email] = []
        by_account[account_email].append(email_data)

    msg = f"📬 **{len(all_emails)} nuove email** in {len(by_account)} account:\n\n"

    for account_email, emails in by_account.items():
        # Find account name
        account_name = account_email
        for key, config in EMAIL_ACCOUNTS.items():
            if config['email'] == account_email:
                account_name = config.get('name', account_email)
                break

        msg += f"**{account_name}** ({len(emails)}):\n"
        for idx, email_data in enumerate(emails[:3], 1):  # Max 3 per account
            msg += f"  • {email_data['from'][:40]}\n"
            msg += f"    _{email_data['subject'][:50]}_\n"

        if len(emails) > 3:
            msg += f"  ... e altre {len(emails) - 3} email\n"
        msg += "\n"

    msg += "\nUsa `/email_switch <account>` per cambiare account"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_email_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email_accounts - lista account"""
    if not is_authorized(update):
        return

    accounts = email_manager.list_accounts()
    current = email_manager.current_account

    msg = "📧 **Account Email Configurati:**\n\n"

    for account in accounts:
        is_current = "⭐" if account['key'] == current else "  "
        status = "✅" if account['configured'] else "⚠️ Password mancante"
        msg += f"{is_current} **{account['name']}**\n"
        msg += f"   Email: `{account['email']}`\n"
        msg += f"   Key: `{account['key']}`\n"
        msg += f"   Status: {status}\n\n"

    msg += "\nUsa `/email_switch <key>` per cambiare account"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_email_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email_switch - cambia account"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Uso: /email_switch <account_key>\n\nUsa /email_accounts per vedere gli account disponibili")
        return

    account_key = context.args[0]

    if email_manager.set_account(account_key):
        account_info = email_manager.get_account_info()
        await update.message.reply_text(f"✅ Account cambiato a: {account_info.get('name', '')} ({account_info.get('email', '')})")
    else:
        await update.message.reply_text(f"❌ Account '{account_key}' non trovato. Usa /email_accounts per vedere gli account disponibili")

async def cmd_email_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email_search - cerca email con filtri"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text(
            "🔍 **Uso:** `/email_search [opzioni]`\n\n"
            "**Opzioni:**\n"
            "`from:<email>` - Cerca per mittente\n"
            "`subject:<testo>` - Cerca per oggetto\n"
            "`account:<key>` - Specifica account (default: corrente)\n\n"
            "**Esempi:**\n"
            "`/email_search from:root@mail.hyperloopitalia.com`\n"
            "`/email_search subject:NormaOS`\n"
            "`/email_search from:root subject:Alert account:info`",
            parse_mode='Markdown'
        )
        return

    # Parse parametri
    from_filter = None
    subject_filter = None
    account_key = None

    for arg in context.args:
        if arg.startswith('from:'):
            from_filter = arg[5:]
        elif arg.startswith('subject:'):
            subject_filter = arg[8:]
        elif arg.startswith('account:'):
            account_key = arg[8:]

    account_info = email_manager.get_account_info(account_key)
    await update.message.reply_text(
        f"🔍 Cerco email in {account_info.get('name', '')}...\n"
        f"From: `{from_filter or 'tutti'}`\n"
        f"Subject: `{subject_filter or 'tutti'}`",
        parse_mode='Markdown'
    )

    emails = email_manager.search_emails(from_filter=from_filter, subject_filter=subject_filter, account_key=account_key)

    if not emails:
        await update.message.reply_text("✅ Nessuna email trovata con questi criteri")
        return

    msg = f"📬 **Trovate {len(emails)} email:**\n\n"
    for idx, email_data in enumerate(emails[:20], 1):  # Max 20 per non sovraccaricare
        msg += f"{idx}. **Da:** {email_data['from'][:50]}\n"
        msg += f"   **Oggetto:** {email_data['subject'][:60]}\n"
        msg += f"   **Data:** {email_data['date'][:30]}\n\n"

    if len(emails) > 20:
        msg += f"\n... e altre {len(emails) - 20} email\n"

    msg += f"\n💡 Usa `/email_delete from:{from_filter or ''} subject:{subject_filter or ''}` per cancellarle"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_email_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /email_delete - cancella email con filtri"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text(
            "🗑️ **Uso:** `/email_delete [opzioni]`\n\n"
            "**Opzioni:**\n"
            "`from:<email>` - Cancella per mittente\n"
            "`subject:<testo>` - Cancella per oggetto\n"
            "`account:<key>` - Specifica account (default: corrente)\n\n"
            "**Esempi:**\n"
            "`/email_delete from:root@mail.hyperloopitalia.com`\n"
            "`/email_delete subject:NormaOS`\n"
            "`/email_delete from:root subject:Alert`\n\n"
            "⚠️ **Attenzione:** Le email verranno cancellate definitivamente!",
            parse_mode='Markdown'
        )
        return

    # Parse parametri
    from_filter = None
    subject_filter = None
    account_key = None

    for arg in context.args:
        if arg.startswith('from:'):
            from_filter = arg[5:]
        elif arg.startswith('subject:'):
            subject_filter = arg[8:]
        elif arg.startswith('account:'):
            account_key = arg[8:]

    account_info = email_manager.get_account_info(account_key)

    # Prima cerca per confermare
    emails = email_manager.search_emails(from_filter=from_filter, subject_filter=subject_filter, account_key=account_key)

    if not emails:
        await update.message.reply_text("✅ Nessuna email trovata con questi criteri")
        return

    await update.message.reply_text(
        f"🗑️ Trovate {len(emails)} email da cancellare in {account_info.get('name', '')}...\n"
        f"Procedo alla cancellazione..."
    )

    # Cancella
    deleted_count = email_manager.search_and_delete(from_filter=from_filter, subject_filter=subject_filter, account_key=account_key)

    await update.message.reply_text(
        f"✅ **Cancellate {deleted_count} email** da {account_info.get('name', '')}\n\n"
        f"From: `{from_filter or 'tutti'}`\n"
        f"Subject: `{subject_filter or 'tutti'}`",
        parse_mode='Markdown'
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /status"""
    if not is_authorized(update):
        return

    await update.message.reply_text("🔍 Recupero status server...")

    status = server_commander.get_server_status()

    msg = "🖥️ **Server Status**\n\n"
    msg += f"⏱️ Uptime: {status.get('uptime', 'N/A')}\n"
    msg += f"💾 Disk: {status.get('disk', 'N/A')}\n"
    msg += f"🧠 Memory: {status.get('memory', 'N/A')}\n"
    msg += f"⚙️ CPU: {status.get('cpu', 'N/A')}%\n"
    msg += f"🔧 Services: {status.get('services', 'N/A')} running\n"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /exec"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Uso: /exec <comando>")
        return

    command = ' '.join(context.args)

    # Whitelist comandi sicuri
    safe_commands = ['ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free', 'ps']
    cmd_base = command.split()[0]

    if cmd_base not in safe_commands:
        await update.message.reply_text(f"⛔ Comando '{cmd_base}' non autorizzato\n\nComandi sicuri: {', '.join(safe_commands)}")
        return

    await update.message.reply_text(f"⚙️ Eseguo: `{command}`", parse_mode='Markdown')

    result = server_commander.execute_command(command)

    if result['success']:
        output = result['stdout'][:2000]  # Max 2000 caratteri
        await update.message.reply_text(f"✅ Output:\n```\n{output}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Error:\n```\n{result['stderr']}\n```", parse_mode='Markdown')

async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /ask - Interroga Claude AI con memoria"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Uso: /ask <domanda>")
        return

    question = ' '.join(context.args)
    await update.message.reply_text("🧠 Sto pensando (con memoria contestuale)...")

    # Track command usage
    memory_manager.track_command_usage('ask')

    # Build context from memory
    memory_context = memory_manager.build_context_for_claude(question)

    # Ask Claude with memory context
    answer = await claude_ai.ask(question, memory_context)

    # Store conversation in memory
    memory_manager.store_conversation(question, answer, message_type='ask')

    await update.message.reply_text(f"🤖 **Claude AI:**\n\n{answer}", parse_mode='Markdown')

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /health - Health check completo"""
    if not is_authorized(update):
        return

    await update.message.reply_text("🏥 Health check in corso...")

    # Check Guardian Bot
    result = server_commander.execute_command('sudo systemctl status guardian-bot --no-pager | head -3')
    guardian_status = "✅ Online" if "active (running)" in result['stdout'] else "❌ Offline"

    # Check Netdata
    result = server_commander.execute_command('sudo systemctl status netdata --no-pager | head -3')
    netdata_status = "✅ Online" if "active (running)" in result['stdout'] else "❌ Offline"

    # Check Healthchecks
    result = server_commander.execute_command('sudo docker ps | grep healthchecks')
    healthchecks_status = "✅ Online" if result['success'] and result['stdout'] else "❌ Offline"

    msg = "🏥 **Health Check Report**\n\n"
    msg += f"🤖 Guardian Bot: {guardian_status}\n"
    msg += f"📊 Netdata: {netdata_status}\n"
    msg += f"🩺 Healthchecks: {healthchecks_status}\n"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /memory - Mostra statistiche memoria"""
    if not is_authorized(update):
        return

    stats = memory_manager.get_usage_stats(days=7)
    profile = memory_manager.get_user_profile()

    msg = "🧬 **Statistiche Memoria LORENZ**\n\n"
    msg += f"📊 **Conversazioni Totali:** {profile.get('total_conversations', 0)}\n"
    msg += f"🕐 **Prima Interazione:** {profile.get('first_interaction', 'N/A')}\n"
    msg += f"🕑 **Ultima Interazione:** {profile.get('last_interaction', 'N/A')}\n\n"

    if stats:
        msg += "📈 **Comandi Più Usati (ultimi 7 giorni):**\n"
        for cmd, count in list(stats.items())[:5]:
            msg += f"  • {cmd}: {count}x\n"
    else:
        msg += "Nessuna statistica disponibile\n"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /profile - Mostra profilo utente"""
    if not is_authorized(update):
        return

    profile = memory_manager.get_user_profile()

    msg = "👤 **Il Tuo Profilo**\n\n"
    msg += f"💬 **Conversazioni:** {profile.get('total_conversations', 0)}\n"
    msg += f"⏱️ **Membro da:** {profile.get('first_interaction', 'N/A')}\n\n"

    if profile.get('top_activities'):
        msg += "🎯 **Attività Principali:**\n"
        for activity, count in profile['top_activities'][:5]:
            msg += f"  • {activity}: {count}x\n"
        msg += "\n"

    if profile.get('preferences'):
        msg += "⚙️ **Preferenze Salvate:**\n"
        for key, value in list(profile['preferences'].items())[:5]:
            msg += f"  • {key}: {value}\n"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /forget - Elimina conversazioni vecchie"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Uso: /forget <days>\n\nEsempio: `/forget 30` per dimenticare conversazioni più vecchie di 30 giorni", parse_mode='Markdown')
        return

    try:
        days = int(context.args[0])
        if days < 1:
            await update.message.reply_text("❌ Il numero di giorni deve essere positivo")
            return

        # TODO: Implementare la cancellazione delle conversazioni vecchie
        await update.message.reply_text(f"🗑️ Funzionalità in arrivo: eliminerò conversazioni più vecchie di {days} giorni")

    except ValueError:
        await update.message.reply_text("❌ Numero giorni non valido")


async def cmd_orchestrator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /orchestrator - Mostra statistiche AI multi-model"""
    if not is_authorized(update):
        return

    if not ai_orchestrator:
        await update.message.reply_text("❌ AI Orchestrator non disponibile")
        return

    stats = ai_orchestrator.get_stats()

    msg = "🧠 **AI Orchestrator - Multi-Model Stats**\n\n"

    # Provider status
    msg += "📡 **Provider Configurati:**\n"
    for provider, enabled in stats.get('providers', {}).items():
        status = "✅" if enabled else "❌"
        msg += f"  {status} {provider.upper()}\n"

    msg += f"\n🎯 **Modelli Disponibili:** {len(stats.get('available_models', []))}\n"
    if stats.get('available_models'):
        for model in stats['available_models'][:8]:
            config = MODELS.get(model, {}) if 'MODELS' in dir() else {}
            msg += f"  • `{model}`\n"

    msg += f"\n📊 **Statistiche Utilizzo:**\n"
    msg += f"  • Richieste totali: {stats.get('total_requests', 0)}\n"
    msg += f"  • Errori: {stats.get('errors', 0)}\n"

    if stats.get('by_provider'):
        msg += "\n📈 **Per Provider:**\n"
        for provider, count in stats['by_provider'].items():
            msg += f"  • {provider}: {count} richieste\n"

    if stats.get('by_task'):
        msg += "\n🔧 **Per Task Type:**\n"
        for task, count in stats['by_task'].items():
            msg += f"  • {task}: {count}\n"

    # Claude stats for comparison
    if claude_ai:
        claude_stats = claude_ai.get_stats()
        msg += f"\n🤖 **Claude Direct Stats:**\n"
        msg += f"  • Haiku: {claude_stats.get('haiku_calls', 0)} chiamate\n"
        msg += f"  • Sonnet: {claude_stats.get('sonnet_calls', 0)} chiamate\n"

    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_ai_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /ai_test - Test rapido dell'AI Orchestrator"""
    if not is_authorized(update):
        return

    if not ai_orchestrator:
        await update.message.reply_text("❌ AI Orchestrator non disponibile")
        return

    await update.message.reply_text("🧪 Test AI Orchestrator in corso...")

    # Test with a simple prompt
    test_prompt = "Dimmi una curiosità interessante in una frase."

    result = await ai_orchestrator.process(test_prompt, prefer_fast=True)

    if result.get('success'):
        msg = f"✅ **Test completato!**\n\n"
        msg += f"**Provider:** {result.get('provider', 'N/A')}\n"
        msg += f"**Modello:** {result.get('model', 'N/A')}\n"
        msg += f"**Task Type:** {result.get('task_type', 'N/A')}\n"
        msg += f"**Tempo:** {result.get('duration_ms', 0):.0f}ms\n\n"
        msg += f"**Risposta:**\n{result.get('response', 'N/A')[:500]}"
    else:
        msg = f"❌ **Test fallito:**\n{result.get('error', 'Unknown error')}"

    await update.message.reply_text(msg, parse_mode='Markdown')


# ============================================================================
# SKILLS COMMANDS
# ============================================================================

async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /skills - Lista tutte le skills disponibili"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Non autorizzato")
        return

    if not skills_manager:
        await update.message.reply_text("❌ Skills System non disponibile")
        return

    # Get control panel data
    data = skills_manager.get_control_panel_data()

    msg = "🎯 **LORENZ SKILLS**\n\n"

    # GOD Skills
    msg += "🌟 **GOD SKILLS** (Built-in)\n"
    msg += "─" * 25 + "\n"
    for skill in data['god_skills']:
        status = "✅" if skill['enabled'] else "❌"
        icon = skill.get('icon', '⚡')
        msg += f"{status} {icon} `{skill['name']}`\n"
        msg += f"    {skill['description_it']}\n"

    # Emergent Skills
    msg += f"\n🧠 **EMERGENT SKILLS** (Learned)\n"
    msg += "─" * 25 + "\n"
    if data['emergent_skills']:
        for skill in data['emergent_skills']:
            status = "✅" if skill['enabled'] else "❌"
            steps = len(skill.get('workflow_steps', []))
            msg += f"{status} 🧠 `{skill['name']}` ({steps} steps)\n"
    else:
        msg += "_(Nessuna skill emergente)_\n"

    # Summary
    msg += f"\n📊 **Riepilogo**\n"
    msg += f"GOD: {data['summary']['enabled_god_skills']}/{data['summary']['total_god_skills']} attive\n"
    msg += f"Emergent: {data['summary']['enabled_emergent_skills']}/{data['summary']['total_emergent_skills']} attive\n"

    msg += "\n💡 Scrivi un messaggio per attivare una skill automaticamente!"

    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /skill <name> [params] - Esegue una skill specifica"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Non autorizzato")
        return

    if not skills_manager:
        await update.message.reply_text("❌ Skills System non disponibile")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Uso: /skill <nome_skill> [parametri]\n\n"
            "Esempi:\n"
            "• `/skill web_search notizie AI`\n"
            "• `/skill server_command uptime`\n"
            "• `/skill image_generation gatto spaziale`"
        , parse_mode='Markdown')
        return

    skill_name = args[0]
    skill_params = ' '.join(args[1:]) if len(args) > 1 else ''

    skill = skills_manager.get_skill(skill_name)
    if not skill:
        enabled = skills_manager.get_enabled_skills()
        await update.message.reply_text(
            f"❌ Skill `{skill_name}` non trovata.\n\n"
            f"Skills disponibili:\n• " + "\n• ".join(enabled)
        , parse_mode='Markdown')
        return

    if not skill.enabled:
        await update.message.reply_text(f"❌ Skill `{skill_name}` è disabilitata")
        return

    skill_type = "🌟 GOD" if skill.skill_type == SkillType.GOD else "🧠 EMERGENT"
    await update.message.reply_text(
        f"⚡ Eseguo: {skill.icon} **{skill.name}** ({skill_type})"
    , parse_mode='Markdown')

    # Execute skill with extracted params
    params = SkillRouter.extract_skill_params(skill_name, skill_params)
    if not params:
        # Fallback: use the rest of the message as main param
        if skill_name == 'web_search':
            params = {'query': skill_params}
        elif skill_name == 'image_generation':
            params = {'prompt': skill_params}
        elif skill_name == 'server_command':
            params = {'command': skill_params}
        elif skill_name == 'web_browse':
            params = {'url': skill_params}

    try:
        result = await skills_manager.execute_skill(skill_name, **params)

        if result.success:
            response = f"{skill.icon} **{skill.name}**\n\n{result.message}"
            if result.artifacts:
                response += "\n\n📎 Allegati:\n"
                for artifact in result.artifacts[:3]:
                    response += f"• {artifact}\n"
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Errore: {result.error}")

    except Exception as e:
        await update.message.reply_text(f"❌ Errore nell'esecuzione: {str(e)}")


async def cmd_mneme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler comando /mneme - Knowledge Base statistics and operations"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Non autorizzato")
        return

    if not skills_manager or not skills_manager.mneme:
        await update.message.reply_text("❌ MNEME Knowledge Base non disponibile")
        return

    mneme = skills_manager.mneme
    args = context.args

    if not args:
        # Show stats
        stats = mneme.get_stats()

        msg = "📚 **MNEME - Knowledge Base**\n\n"
        msg += f"📊 **Statistiche**\n"
        msg += f"• Entries totali: {stats.get('total_entries', 0)}\n"
        msg += f"• Skills emergenti: {stats.get('total_skills', 0)}\n"

        if stats.get('by_category'):
            msg += f"\n📁 **Per categoria:**\n"
            for cat, count in stats['by_category'].items():
                msg += f"  • {cat}: {count}\n"

        if stats.get('recent_activity'):
            msg += f"\n🕐 **Attività recente:**\n"
            for activity in stats['recent_activity'][:5]:
                msg += f"  • {activity['title']} ({activity['category']})\n"

        msg += "\n💡 **Comandi:**\n"
        msg += "• `/mneme search <query>` - Cerca\n"
        msg += "• `/mneme export` - Esporta JSON\n"
        msg += "• `/mneme add <title> | <content>` - Aggiungi\n"

        await update.message.reply_text(msg, parse_mode='Markdown')

    elif args[0] == 'search' and len(args) > 1:
        query = ' '.join(args[1:])
        entries = mneme.search_knowledge(query=query, limit=5)

        if entries:
            msg = f"🔍 **Risultati per '{query}':**\n\n"
            for entry in entries:
                msg += f"• **{entry.title}** [{entry.category}]\n"
                msg += f"  {entry.content[:100]}...\n\n"
        else:
            msg = f"❌ Nessun risultato per '{query}'"

        await update.message.reply_text(msg, parse_mode='Markdown')

    elif args[0] == 'export':
        json_data = mneme.export_to_json()
        # Send as file
        from io import BytesIO
        file_buffer = BytesIO(json_data.encode('utf-8'))
        file_buffer.name = f"mneme_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        await update.message.reply_document(
            document=file_buffer,
            caption="📚 MNEME Knowledge Base Export"
        )

    elif args[0] == 'add' and len(args) > 1:
        # Format: /mneme add Title | Content
        full_text = ' '.join(args[1:])
        if '|' in full_text:
            parts = full_text.split('|', 1)
            title = parts[0].strip()
            content = parts[1].strip()

            from lorenz_skills import KnowledgeEntry
            entry = KnowledgeEntry(
                id="",
                category="fact",
                title=title,
                content=content,
                source="telegram_command"
            )

            if mneme.add_knowledge(entry):
                await update.message.reply_text(f"✅ Aggiunto: **{title}**", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Errore nell'aggiunta")
        else:
            await update.message.reply_text("❌ Formato: `/mneme add Titolo | Contenuto`", parse_mode='Markdown')

    else:
        await update.message.reply_text(
            "❌ Comando non riconosciuto.\n\n"
            "Uso:\n"
            "• `/mneme` - Statistiche\n"
            "• `/mneme search <query>` - Cerca\n"
            "• `/mneme export` - Esporta\n"
            "• `/mneme add <title> | <content>` - Aggiungi"
        , parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler messaggi generici - Skills + AI Chat

    Ordine di elaborazione:
    1. Rileva se il messaggio corrisponde a una SKILL (GOD o Emergent)
    2. Se sì, esegue la skill e ritorna il risultato
    3. Se no, usa AI Chat con RAG/memoria
    """
    if not is_authorized(update):
        return

    text = update.message.text

    try:
        # =====================================================================
        # STEP 1: Check if message matches a SKILL
        # =====================================================================
        if skill_router and skills_manager:
            detected_skill = skill_router.detect_skill(text)

            if detected_skill:
                # Skill detected! Execute it
                skill = skills_manager.get_skill(detected_skill)
                skill_type = "🌟 GOD" if skill.skill_type == SkillType.GOD else "🧠 EMERGENT"

                await update.message.reply_text(
                    f"⚡ Eseguo skill: {skill.icon} **{skill.name}** ({skill_type})"
                )

                # Extract parameters from text
                params = SkillRouter.extract_skill_params(detected_skill, text)
                logger.info(f"🎯 Executing skill '{detected_skill}' with params: {params}")

                # Execute skill
                result = await skills_manager.execute_skill(detected_skill, **params)

                if result.success:
                    response = f"{skill.icon} **{skill.name}**\n\n{result.message}"

                    # Add artifacts if any (URLs, file paths)
                    if result.artifacts:
                        response += "\n\n📎 Allegati:\n"
                        for artifact in result.artifacts[:3]:  # Max 3 artifacts
                            response += f"• {artifact}\n"

                    await update.message.reply_text(response, parse_mode='Markdown')
                else:
                    await update.message.reply_text(
                        f"❌ Skill {skill.name} fallita:\n{result.error}"
                    )

                # Store in memory/RAG
                if memory_manager:
                    memory_manager.store_conversation(
                        text, result.message,
                        message_type=f'skill_{detected_skill}'
                    )

                return  # Done, don't proceed to AI chat

        # =====================================================================
        # STEP 2: No skill matched - Use AI Chat
        # =====================================================================
        await update.message.reply_text("🧠 Pensando...")

        # Build context
        context_info = ""

        # Add server context if relevant
        if any(word in text.lower() for word in ['server', 'servizio', 'sistema', 'errore', 'problema', 'status']):
            status = server_commander.get_server_status()
            context_info += f"Server Status:\n{json.dumps(status, indent=2)}\n\n"

        # Add available skills to context
        if skills_manager:
            enabled_skills = skills_manager.get_enabled_skills()
            context_info += f"Available skills: {', '.join(enabled_skills)}\n\n"

        # Use RAG if available, otherwise basic memory
        if rag_system:
            # Store conversation in RAG
            rag_system.add_document(
                content=f"User: {text}",
                metadata={'type': 'user_message', 'timestamp': datetime.now().isoformat()}
            )

            # Retrieve relevant context
            rag_context = rag_system.build_context(text, max_tokens=1500)
            full_context = context_info + rag_context

            logger.info(f"🔍 RAG context: {len(rag_context)} chars")

        elif memory_manager:
            # Fallback to basic memory
            memory_manager.track_command_usage('chat')
            memory_context = memory_manager.build_context_for_claude(text)
            full_context = context_info + memory_context

        else:
            full_context = context_info

        # Ask AI (with intelligent routing via Orchestrator or Claude)
        model_info = ""
        if ai_orchestrator and ai_orchestrator.has_available_provider():
            # Use multi-model orchestrator
            result = await ai_orchestrator.process(text, context=full_context)
            if result.get('success'):
                answer = result.get('response', '')
                model_used = result.get('model', 'unknown')
                provider = result.get('provider', 'unknown')
                duration = result.get('duration_ms', 0)
                model_info = f"\n\n_[{provider}/{model_used} • {duration:.0f}ms]_"
                logger.info(f"🎯 Used AI Orchestrator: {provider}/{model_used} in {duration:.0f}ms")
            else:
                # Orchestrator failed, fallback to Claude
                logger.warning(f"⚠️ Orchestrator failed: {result.get('error')}, falling back to Claude")
                answer = await claude_ai.ask(text, full_context)
        else:
            # Fallback to Claude
            answer = await claude_ai.ask(text, full_context)

        # Store response in RAG
        if rag_system:
            rag_system.add_document(
                content=f"Assistant: {answer}",
                metadata={'type': 'assistant_response', 'timestamp': datetime.now().isoformat()}
            )
        elif memory_manager:
            memory_manager.store_conversation(text, answer, message_type='chat')

        await update.message.reply_text(f"🤖 {answer}{model_info}", parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)}\n\nUsa /help per vedere i comandi disponibili")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler errori"""
    logger.error(f"Update {update} caused error {context.error}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main function"""
    logger.info("🚀 Starting LORENZ...")

    # Verifica token
    if TELEGRAM_BOT_TOKEN == 'YOUR_NEW_BOT_TOKEN_HERE':
        logger.error("❌ TELEGRAM_BOT_TOKEN non configurato!")
        sys.exit(1)

    # Crea application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Registra handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("email", cmd_email))
    app.add_handler(CommandHandler("email_all", cmd_email_all))
    app.add_handler(CommandHandler("email_accounts", cmd_email_accounts))
    app.add_handler(CommandHandler("email_switch", cmd_email_switch))
    app.add_handler(CommandHandler("email_search", cmd_email_search))
    app.add_handler(CommandHandler("email_delete", cmd_email_delete))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("exec", cmd_exec))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("forget", cmd_forget))

    # AI Orchestrator commands
    app.add_handler(CommandHandler("orchestrator", cmd_orchestrator))
    app.add_handler(CommandHandler("ai_test", cmd_ai_test))

    # Skills System commands
    app.add_handler(CommandHandler("skills", cmd_skills))
    app.add_handler(CommandHandler("skill", cmd_skill))
    app.add_handler(CommandHandler("mneme", cmd_mneme))

    # Handler messaggi generici
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    app.add_error_handler(error_handler)

    # Start bot
    logger.info("✅ LORENZ is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
