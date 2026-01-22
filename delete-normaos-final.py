#!/usr/bin/env python3
"""
Cancella email NormaOS da bibop@bibop.com
"""

import imaplib
import email as email_module

ACCOUNT = {
    'email': 'bibop@bibop.com',
    'imap_host': 'mail.hyperloopitalia.com',
    'imap_port': 993,
    'password': 'bibOb1b0P2026Ab@'
}

def delete_normaos_emails():
    """Cancella tutte le email NormaOS Alert da root@mail.hyperloopitalia.com"""
    print("🚀 Cancellazione Email NormaOS Alert")
    print("="*60)

    try:
        # Connessione
        print("📡 Connessione IMAP...")
        mail = imaplib.IMAP4_SSL(ACCOUNT['imap_host'], ACCOUNT['imap_port'])
        mail.login(ACCOUNT['email'], ACCOUNT['password'])
        print("✅ Connesso")

        mail.select('INBOX')

        # Cerca email da root@mail.hyperloopitalia.com
        print("\n🔍 Ricerca email da root@mail.hyperloopitalia.com...")
        _, message_numbers = mail.search(None, 'FROM "root@mail.hyperloopitalia.com"')
        email_ids = message_numbers[0].split()

        print(f"📧 Trovate {len(email_ids)} email")

        if not email_ids:
            print("✅ Nessuna email da cancellare!")
            mail.close()
            mail.logout()
            return 0

        # Mostra prime 3
        print("\n📬 Prime 3 email:")
        for num in email_ids[:3]:
            _, msg_data = mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            message = email_module.message_from_bytes(email_body)
            print(f"  - Oggetto: {message.get('Subject', 'No Subject')[:60]}")
            print(f"    Data: {message.get('Date', '')[:40]}")

        # Cancella tutte
        print(f"\n🗑️  Cancellazione di {len(email_ids)} email...")
        deleted_count = 0

        for email_id in email_ids:
            try:
                mail.store(email_id, '+FLAGS', '\\Deleted')
                deleted_count += 1

                if deleted_count % 10 == 0:
                    print(f"  ⏳ {deleted_count}/{len(email_ids)}...")

            except Exception as e:
                print(f"  ❌ Errore email {email_id.decode()}: {e}")

        # Expunge
        print("\n♻️  Rimozione definitiva...")
        mail.expunge()

        mail.close()
        mail.logout()

        print("\n" + "="*60)
        print(f"✅ COMPLETATO! Cancellate {deleted_count}/{len(email_ids)} email")
        print("="*60)

        return deleted_count

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    delete_normaos_emails()
