#!/usr/bin/env python3
"""
Script per trovare dove sono le email NormaOS
"""

import os
import sys
import imaplib
import email as email_module

# Multi-Account Email Configuration
EMAIL_ACCOUNTS = {
    'info': {
        'email': 'info@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'password': 'infOB1b0p2026Ai@',
    },
    'norma': {
        'email': 'norma@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'password': 'N0rm@B1b0p2025!',
    },
    'lorenz': {
        'email': 'lorenz@bibop.com',
        'imap_host': 'mail.hyperloopitalia.com',
        'imap_port': 993,
        'password': 'lorEb1b0P2026Al@',
    }
}

def check_account(account_key, account_config):
    """Controlla un account per email NormaOS"""
    print(f"\n{'='*60}")
    print(f"🔍 Controllo: {account_config['email']}")
    print(f"{'='*60}")

    try:
        mail = imaplib.IMAP4_SSL(account_config['imap_host'], account_config['imap_port'])
        mail.login(account_config['email'], account_config['password'])
        print(f"✅ Connesso con successo")

        mail.select('INBOX')

        # Cerca per subject "NormaOS"
        _, message_numbers = mail.search(None, 'SUBJECT "NormaOS"')
        email_ids = message_numbers[0].split()

        print(f"📧 Trovate {len(email_ids)} email con subject 'NormaOS'")

        if email_ids:
            print(f"\n⭐ TROVATE! Le email NormaOS sono in {account_config['email']}")

            # Mostra prime 3
            print("\n📬 Prime 3 email:")
            for num in email_ids[:3]:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email_module.message_from_bytes(email_body)
                print(f"  - Da: {message.get('From', 'Unknown')[:60]}")
                print(f"    Oggetto: {message.get('Subject', 'No Subject')[:60]}")
                print(f"    Data: {message.get('Date', '')[:40]}")

        mail.close()
        mail.logout()

        return len(email_ids)

    except Exception as e:
        print(f"❌ Errore: {e}")
        return 0

def main():
    print("🚀 Ricerca Email NormaOS in tutti gli account")
    print("="*60)

    total_found = 0
    accounts_with_emails = []

    for key, config in EMAIL_ACCOUNTS.items():
        count = check_account(key, config)
        total_found += count
        if count > 0:
            accounts_with_emails.append((config['email'], count))

    print(f"\n{'='*60}")
    print(f"📊 RIEPILOGO")
    print(f"{'='*60}")
    print(f"Totale email NormaOS trovate: {total_found}")

    if accounts_with_emails:
        print(f"\nAccount con email NormaOS:")
        for email, count in accounts_with_emails:
            print(f"  - {email}: {count} email")
    else:
        print("\n✅ Nessuna email NormaOS trovata in nessun account!")

if __name__ == '__main__':
    main()
