#!/usr/bin/env python3
"""
Test connessione IMAP per bibop@bibop.com
"""

import imaplib
import email as email_module

ACCOUNT = {
    'email': 'bibop@bibop.com',
    'imap_host': 'mail.hyperloopitalia.com',
    'imap_port': 993,
    'password': 'bibOb1b0P2026Ab@'
}

print(f"🔍 Test connessione a {ACCOUNT['email']}")
print(f"📡 Server: {ACCOUNT['imap_host']}:{ACCOUNT['imap_port']}")
print(f"🔐 Password: {ACCOUNT['password'][:4]}...{ACCOUNT['password'][-4:]}")
print("="*60)

try:
    print("\n1️⃣ Connessione SSL...")
    mail = imaplib.IMAP4_SSL(ACCOUNT['imap_host'], ACCOUNT['imap_port'])
    print("✅ SSL connesso")

    print("\n2️⃣ Login...")
    result = mail.login(ACCOUNT['email'], ACCOUNT['password'])
    print(f"✅ Login riuscito: {result}")

    print("\n3️⃣ Selezione INBOX...")
    mail.select('INBOX')
    print("✅ INBOX selezionato")

    print("\n4️⃣ Ricerca email NormaOS...")
    # Prova vari filtri
    filters = [
        ('SUBJECT "NormaOS"', 'Subject: NormaOS'),
        ('SUBJECT "Health Check"', 'Subject: Health Check'),
        ('FROM "root@mail.hyperloopitalia.com"', 'From: root@mail.hyperloopitalia.com'),
        ('TO "admin@bibop.com"', 'To: admin@bibop.com'),
        ('ALL', 'Tutte le email')
    ]

    for search_filter, description in filters:
        _, message_numbers = mail.search(None, search_filter)
        email_ids = message_numbers[0].split()
        print(f"  {description}: {len(email_ids)} email")

        if len(email_ids) > 0 and search_filter != 'ALL':
            print(f"\n  📧 Prima email trovata:")
            _, msg_data = mail.fetch(email_ids[0], '(RFC822)')
            email_body = msg_data[0][1]
            message = email_module.message_from_bytes(email_body)
            print(f"    Da: {message.get('From', 'Unknown')}")
            print(f"    A: {message.get('To', 'Unknown')}")
            print(f"    Oggetto: {message.get('Subject', 'No Subject')}")
            print(f"    Data: {message.get('Date', '')}")

    mail.close()
    mail.logout()
    print("\n✅ Test completato con successo!")

except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
