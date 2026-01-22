#!/usr/bin/env python3
"""
Script per cancellare tutte le email NormaOS Health Check
"""

import os
import sys
import imaplib
import email as email_module

# Importa configurazione da lorenz-bot.py
sys.path.insert(0, os.path.dirname(__file__))

# Multi-Account Email Configuration (copia da lorenz-bot.py)
EMAIL_ACCOUNTS = {
    'info': {
        'email': 'info@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': 'infOB1b0p2026Ai@',
        'name': '📧 Info Bibop'
    },
    'bibop': {
        'email': 'bibop@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'smtp_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'smtp_port': 587,
        'password': os.getenv('EMAIL_BIBOP_PASSWORD', 'bibOb1b0P2026Ab@'),
        'name': '👤 Bibop Personal'
    }
}

# Usa account bibop@bibop.com (dove arrivano le email di admin@bibop.com)
ACCOUNT = EMAIL_ACCOUNTS['bibop']

print(f"🔍 Usando account: {ACCOUNT['email']}")
print(f"🔐 Password configurata: {'✅' if ACCOUNT['password'] else '❌'}")

def connect_imap():
    """Connessione IMAP"""
    try:
        mail = imaplib.IMAP4_SSL(ACCOUNT['imap_host'], ACCOUNT['imap_port'])
        mail.login(ACCOUNT['email'], ACCOUNT['password'])
        return mail
    except Exception as e:
        print(f"❌ Errore connessione IMAP: {e}")
        return None

def search_normaos_emails():
    """Cerca tutte le email NormaOS"""
    mail = connect_imap()
    if not mail:
        return []

    try:
        mail.select('INBOX')

        # Cerca per subject "NormaOS"
        _, message_numbers = mail.search(None, 'SUBJECT "NormaOS"')

        email_ids = message_numbers[0].split()
        print(f"🔍 Trovate {len(email_ids)} email con subject 'NormaOS'")

        # Mostra prime 5 per conferma
        if email_ids:
            print("\n📧 Prime 5 email trovate:")
            for num in email_ids[:5]:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                print(f"  - Da: {message.get('From', 'Unknown')}")
                print(f"    Oggetto: {message.get('Subject', 'No Subject')}")
                print(f"    Data: {message.get('Date', '')}")

        mail.close()
        mail.logout()
        return [num.decode() for num in email_ids]

    except Exception as e:
        print(f"❌ Errore ricerca: {e}")
        return []

def delete_emails(email_ids):
    """Cancella email per ID"""
    if not email_ids:
        print("✅ Nessuna email da cancellare")
        return 0

    mail = connect_imap()
    if not mail:
        return 0

    try:
        mail.select('INBOX')

        deleted_count = 0
        for email_id in email_ids:
            try:
                # Marca come Deleted
                mail.store(email_id.encode(), '+FLAGS', '\\Deleted')
                deleted_count += 1

                # Progress ogni 10 email
                if deleted_count % 10 == 0:
                    print(f"⏳ Cancellate {deleted_count}/{len(email_ids)} email...")

            except Exception as e:
                print(f"❌ Errore cancellazione email {email_id}: {e}")

        # Esegui expunge per rimuovere definitivamente
        print("🗑️  Rimozione definitiva...")
        mail.expunge()

        mail.close()
        mail.logout()

        print(f"✅ Cancellate {deleted_count} email da {ACCOUNT['email']}")
        return deleted_count

    except Exception as e:
        print(f"❌ Errore cancellazione batch: {e}")
        return 0

def main():
    print("🚀 Script Cancellazione Email NormaOS")
    print("=" * 50)
    print(f"Account: {ACCOUNT['email']}")
    print("=" * 50)

    # Cerca email
    email_ids = search_normaos_emails()

    if not email_ids:
        print("\n✅ Nessuna email NormaOS trovata!")
        return

    # Conferma cancellazione
    print(f"\n⚠️  Trovate {len(email_ids)} email da cancellare")
    confirm = input("Procedo con la cancellazione? (si/no): ").lower()

    if confirm not in ['si', 's', 'yes', 'y']:
        print("❌ Cancellazione annullata")
        return

    # Cancella
    print("\n🗑️  Cancellazione in corso...")
    deleted_count = delete_emails(email_ids)

    print("\n" + "=" * 50)
    print(f"✅ COMPLETATO! Cancellate {deleted_count} email")
    print("=" * 50)

if __name__ == '__main__':
    main()
