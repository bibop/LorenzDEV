#!/usr/bin/env python3
import imaplib
import email as email_module

ACCOUNT = {
    'email': 'bibop@bibop.com',
    'imap_host': 'mail.hyperloopitalia.com',
    'imap_port': 993,
    'password': 'bibOb1b0P2026Ab@'
}

mail = imaplib.IMAP4_SSL(ACCOUNT['imap_host'], ACCOUNT['imap_port'])
mail.login(ACCOUNT['email'], ACCOUNT['password'])
mail.select('INBOX')

_, message_numbers = mail.search(None, 'TO "admin@bibop.com"')
email_ids = message_numbers[0].split()

print(f"📧 Trovate {len(email_ids)} email con To: admin@bibop.com\n")

for num in email_ids:
    _, msg_data = mail.fetch(num, '(RFC822)')
    email_body = msg_data[0][1]
    message = email_module.message_from_bytes(email_body)

    print("="*60)
    print(f"Da: {message.get('From', 'Unknown')}")
    print(f"A: {message.get('To', 'Unknown')}")
    print(f"Oggetto: {message.get('Subject', 'No Subject')}")
    print(f"Data: {message.get('Date', '')}")

    # Body preview
    body = ""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                break
    else:
        body = message.get_payload(decode=True).decode('utf-8', errors='ignore')

    print(f"\nAnteprima:\n{body[:200]}")
    print("="*60)

mail.close()
mail.logout()
