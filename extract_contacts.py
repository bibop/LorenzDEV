#!/usr/bin/env python3
"""
Estrattore contatti email per LORENZ
Estrae tutti i contatti unici da più account email
"""

import imaplib
import ssl
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import json
import re
from collections import defaultdict
from datetime import datetime
import sys

# Configurazione account
ACCOUNTS = [
    {
        'email': 'bibop@hyperloopitalia.com',
        'host': 'mail.hyperloopitalia.com',
        'port': 993,
        'password': 'HyperB1b0p2026Ah@',
        'ssl_verify': True
    },
    {
        'email': 'bibop@bibop.com',
        'host': 'mail.hyperloopitalia.com',
        'port': 993,
        'password': 'bibOb1b0P2026Ab@',
        'ssl_verify': True
    },
    {
        'email': 'bibop@wdfholding.com',
        'host': 'mail.hyperloopitalia.com',
        'port': 993,
        'password': 'wdfhOb1b0P2026Aw@',
        'ssl_verify': True
    }
]

# Pattern per escludere email spam/newsletter/noreply
EXCLUDE_PATTERNS = [
    r'noreply@',
    r'no-reply@',
    r'notification@',
    r'notifications@',
    r'mailer-daemon@',
    r'postmaster@',
    r'bounce@',
    r'unsubscribe@',
    r'newsletter@',
    r'marketing@',
    r'support@.*\.(com|io|net)$',  # Solo support generici
    r'info@.*\.(linkedin|facebook|twitter|google|microsoft|apple)',
    r'root@mail\.hyperloopitalia\.com',
    r'@normaos\.com$',
]

def decode_str(s):
    """Decodifica header email"""
    if s is None:
        return ""
    decoded = []
    for part, charset in decode_header(s):
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(charset or 'utf-8', errors='ignore'))
            except:
                decoded.append(part.decode('utf-8', errors='ignore'))
        else:
            decoded.append(str(part))
    return ''.join(decoded)

def extract_email_address(s):
    """Estrae email e nome da stringa"""
    name, email_addr = parseaddr(s)
    name = decode_str(name)
    return name.strip(), email_addr.lower().strip()

def is_excluded(email_addr):
    """Verifica se l'email va esclusa"""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, email_addr, re.IGNORECASE):
            return True
    return False

def connect_imap(account):
    """Connessione IMAP"""
    context = ssl.create_default_context()
    if not account.get('ssl_verify', True):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    mail = imaplib.IMAP4_SSL(account['host'], account['port'], ssl_context=context)
    mail.login(account['email'], account['password'])
    return mail

def extract_contacts_from_account(account, max_messages=5000):
    """Estrae contatti da un account email"""
    contacts = defaultdict(lambda: {
        'name': '',
        'email': '',
        'sources': set(),
        'interaction_types': set(),
        'subjects': [],
        'first_contact': None,
        'last_contact': None,
        'count': 0
    })

    print(f"\n{'='*60}")
    print(f"📧 Processing: {account['email']}")
    print(f"{'='*60}")

    try:
        mail = connect_imap(account)

        # Seleziona INBOX
        mail.select('INBOX')

        # Cerca tutte le email
        _, messages = mail.search(None, 'ALL')
        message_nums = messages[0].split()
        total = len(message_nums)

        print(f"   Totale messaggi: {total}")

        # Limita ai messaggi più recenti
        if total > max_messages:
            message_nums = message_nums[-max_messages:]
            print(f"   Processando ultimi {max_messages} messaggi...")

        processed = 0
        for num in message_nums:
            try:
                # Fetch solo headers (più veloce)
                _, msg_data = mail.fetch(num, '(RFC822.HEADER)')
                if not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Estrai data
                date_str = msg.get('Date')
                msg_date = None
                if date_str:
                    try:
                        msg_date = parsedate_to_datetime(date_str)
                    except:
                        pass

                # Estrai subject
                subject = decode_str(msg.get('Subject', ''))[:100]

                # Estrai FROM (chi ci scrive)
                from_header = msg.get('From', '')
                from_name, from_email = extract_email_address(from_header)

                if from_email and not is_excluded(from_email):
                    c = contacts[from_email]
                    if from_name and not c['name']:
                        c['name'] = from_name
                    c['email'] = from_email
                    c['sources'].add(account['email'])
                    c['interaction_types'].add('RICEVUTO')
                    c['count'] += 1
                    if subject and len(c['subjects']) < 5:
                        c['subjects'].append(subject)
                    if msg_date:
                        if not c['first_contact'] or msg_date < c['first_contact']:
                            c['first_contact'] = msg_date
                        if not c['last_contact'] or msg_date > c['last_contact']:
                            c['last_contact'] = msg_date

                # Estrai TO (a chi scriviamo)
                to_header = msg.get('To', '')
                for addr in to_header.split(','):
                    to_name, to_email = extract_email_address(addr)
                    if to_email and not is_excluded(to_email) and to_email != account['email'].lower():
                        c = contacts[to_email]
                        if to_name and not c['name']:
                            c['name'] = to_name
                        c['email'] = to_email
                        c['sources'].add(account['email'])
                        c['interaction_types'].add('INVIATO')
                        c['count'] += 1
                        if subject and len(c['subjects']) < 5:
                            c['subjects'].append(subject)
                        if msg_date:
                            if not c['first_contact'] or msg_date < c['first_contact']:
                                c['first_contact'] = msg_date
                            if not c['last_contact'] or msg_date > c['last_contact']:
                                c['last_contact'] = msg_date

                processed += 1
                if processed % 500 == 0:
                    print(f"   Processati: {processed}/{len(message_nums)} - Contatti unici: {len(contacts)}")

            except Exception as e:
                continue

        mail.logout()
        print(f"   ✅ Completato! Contatti estratti: {len(contacts)}")

    except Exception as e:
        print(f"   ❌ Errore: {e}")

    return contacts

def merge_contacts(all_contacts, new_contacts):
    """Merge contatti da più fonti"""
    for email_addr, data in new_contacts.items():
        if email_addr in all_contacts:
            existing = all_contacts[email_addr]
            if data['name'] and not existing['name']:
                existing['name'] = data['name']
            existing['sources'].update(data['sources'])
            existing['interaction_types'].update(data['interaction_types'])
            existing['subjects'].extend(data['subjects'][:3])
            existing['count'] += data['count']
            if data['first_contact']:
                if not existing['first_contact'] or data['first_contact'] < existing['first_contact']:
                    existing['first_contact'] = data['first_contact']
            if data['last_contact']:
                if not existing['last_contact'] or data['last_contact'] > existing['last_contact']:
                    existing['last_contact'] = data['last_contact']
        else:
            all_contacts[email_addr] = data

def save_contacts(contacts, output_file):
    """Salva contatti in JSON"""
    # Converti per serializzazione JSON
    output = []
    for email_addr, data in contacts.items():
        output.append({
            'nome': data['name'] or extract_name_from_email(email_addr),
            'email': email_addr,
            'account_origine': list(data['sources']),
            'tipo_interazione': list(data['interaction_types']),
            'num_interazioni': data['count'],
            'primo_contatto': data['first_contact'].isoformat() if data['first_contact'] else None,
            'ultimo_contatto': data['last_contact'].isoformat() if data['last_contact'] else None,
            'argomenti': list(set(data['subjects']))[:5]
        })

    # Ordina per numero interazioni (decrescente)
    output.sort(key=lambda x: x['num_interazioni'], reverse=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return output

def extract_name_from_email(email_addr):
    """Estrae nome da indirizzo email"""
    local = email_addr.split('@')[0]
    # Rimuovi numeri e caratteri speciali
    name = re.sub(r'[._-]', ' ', local)
    name = re.sub(r'\d+', '', name)
    return name.title().strip()

def main():
    print("="*60)
    print("🔍 LORENZ Contact Extractor")
    print("="*60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Account da processare: {len(ACCOUNTS)}")

    all_contacts = {}

    for account in ACCOUNTS:
        contacts = extract_contacts_from_account(account, max_messages=5000)
        merge_contacts(all_contacts, contacts)
        print(f"   Totale contatti finora: {len(all_contacts)}")

    # Salva risultati
    output_file = '/Users/bibop/Documents/AI/Lorenz/output/contatti_estratti.json'
    contacts_list = save_contacts(all_contacts, output_file)

    print("\n" + "="*60)
    print("📊 RIEPILOGO FINALE")
    print("="*60)
    print(f"Contatti totali estratti: {len(contacts_list)}")
    print(f"File salvato: {output_file}")

    # Top 10 contatti per interazioni
    print("\n📈 Top 10 contatti per numero interazioni:")
    for i, c in enumerate(contacts_list[:10], 1):
        print(f"   {i}. {c['nome']} <{c['email']}> - {c['num_interazioni']} interazioni")

    return contacts_list

if __name__ == '__main__':
    main()
