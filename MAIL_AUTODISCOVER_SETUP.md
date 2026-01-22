# MAIL AUTODISCOVER ENTERPRISE SETUP

Configurazione enterprise per autodiscovery email su tutti i domini Postfix.
Server: **mail.hyperloopitalia.com** (80.240.31.197)

## Domini Email Configurati

| Dominio | Autodiscover | Autoconfig |
|---------|--------------|------------|
| bibop.com | autodiscover.bibop.com | autoconfig.bibop.com |
| hyper.works | autodiscover.hyper.works | autoconfig.hyper.works |
| hyperloopitalia.com | autodiscover.hyperloopitalia.com | autoconfig.hyperloopitalia.com |
| hyperlabai.com | autodiscover.hyperlabai.com | autoconfig.hyperlabai.com |
| hyperloop.ventures | autodiscover.hyperloop.ventures | autoconfig.hyperloop.ventures |
| wdfholding.com | autodiscover.wdfholding.com | autoconfig.wdfholding.com |
| hyper-works.com | autodiscover.hyper-works.com | autoconfig.hyper-works.com |

---

## RECORD DNS RICHIESTI (per ogni dominio)

### Record A (puntano al server Vultr)

```dns
autodiscover    A    80.240.31.197
autoconfig      A    80.240.31.197
```

### Record SRV (alternativi, per client che li supportano)

```dns
_autodiscover._tcp    SRV    0 0 443 mail.hyperloopitalia.com.
_imaps._tcp           SRV    0 0 993 mail.hyperloopitalia.com.
_submission._tcp      SRV    0 0 587 mail.hyperloopitalia.com.
```

---

## PROCEDURA: Aggiungere Nuovo Dominio Email

### Step 1: Creare dominio in PostfixAdmin

```bash
ssh linuxuser@80.240.31.197
sudo mysql -u root postfixadmin -e "
INSERT INTO domain (domain, description, aliases, mailboxes, maxquota, quota, transport, backupmx, active)
VALUES ('nuovo-dominio.com', 'Descrizione', 100, 100, 10240, 0, 'virtual', 0, 1);
"
```

### Step 2: Creare mailbox

```bash
# Genera hash password
PASS_HASH=$(doveadm pw -s SHA512-CRYPT -p "PasswordUtente123!")

# Crea mailbox
sudo mysql -u root postfixadmin -e "
INSERT INTO mailbox (username, password, name, maildir, quota, local_part, domain, created, modified, active)
VALUES (
    'utente@nuovo-dominio.com',
    '$PASS_HASH',
    'Nome Utente',
    'nuovo-dominio.com/utente/',
    0,
    'utente',
    'nuovo-dominio.com',
    NOW(), NOW(), 1
);
"

# Crea alias
sudo mysql -u root postfixadmin -e "
INSERT INTO alias (address, goto, domain, created, modified, active)
VALUES ('utente@nuovo-dominio.com', 'utente@nuovo-dominio.com', 'nuovo-dominio.com', NOW(), NOW(), 1);
"

# Crea directory
sudo mkdir -p /var/vmail/nuovo-dominio.com/utente
sudo chown -R vmail:vmail /var/vmail/nuovo-dominio.com
```

### Step 3: Aggiungere dominio a Autodiscover

Modificare `/var/www/autodiscover/autodiscover/autodiscover.php`:
```php
$SUPPORTED_DOMAINS = [
    "bibop.com",
    // ... altri domini ...
    "nuovo-dominio.com"  // <-- Aggiungere qui
];
```

Modificare `/var/www/autodiscover/autoconfig.php`:
```php
<domain>nuovo-dominio.com</domain>  <!-- Aggiungere -->
```

### Step 4: Configurare DNS

Aggiungere questi record DNS per `nuovo-dominio.com`:

```dns
; Record MX (per ricevere email)
@               MX    10    mail.hyperloopitalia.com.

; Record SPF (per inviare email)
@               TXT   "v=spf1 mx a:mail.hyperloopitalia.com ~all"

; Record Autodiscover
autodiscover    A     80.240.31.197
autoconfig      A     80.240.31.197

; Record SRV (opzionali ma consigliati)
_autodiscover._tcp    SRV    0 0 443 mail.hyperloopitalia.com.
_imaps._tcp           SRV    0 0 993 mail.hyperloopitalia.com.
_submission._tcp      SRV    0 0 587 mail.hyperloopitalia.com.

; DKIM (generare chiave specifica)
; DMARC
_dmarc          TXT   "v=DMARC1; p=quarantine; rua=mailto:admin@bibop.com"
```

### Step 5: Generare certificato SSL (dopo DNS)

```bash
sudo certbot certonly --nginx \
    -d autodiscover.nuovo-dominio.com \
    -d autoconfig.nuovo-dominio.com \
    --non-interactive --agree-tos --email admin@bibop.com
```

### Step 6: Ricaricare servizi

```bash
sudo systemctl reload postfix
sudo systemctl reload dovecot
sudo systemctl reload nginx
```

---

## CONFIGURAZIONE CLIENT EMAIL

### Outlook (Windows/Mac)
1. Aggiungi account
2. Inserisci email e password
3. Autodiscover configura automaticamente

### iOS/macOS Mail
1. Impostazioni > Mail > Account > Aggiungi
2. Seleziona "Altro"
3. Inserisci email e password
4. Il sistema trova automaticamente le impostazioni

### Thunderbird
1. File > Nuovo > Account email esistente
2. Inserisci nome, email, password
3. Autoconfig trova le impostazioni

### Configurazione Manuale (fallback)
```
Server IMAP: mail.hyperloopitalia.com
Porta IMAP: 993 (SSL/TLS)
Server SMTP: mail.hyperloopitalia.com
Porta SMTP: 587 (STARTTLS)
Username: email completa (es: utente@dominio.com)
```

---

## FILE SUL SERVER

| File | Descrizione |
|------|-------------|
| `/var/www/autodiscover/autodiscover/autodiscover.php` | Endpoint Outlook |
| `/var/www/autodiscover/autoconfig.php` | Endpoint Thunderbird |
| `/etc/nginx/sites-available/autodiscover` | Config Nginx |
| `/var/log/autodiscover.log` | Log richieste |

---

## TROUBLESHOOTING

### Verificare Autodiscover
```bash
# Test Outlook autodiscover
curl -X POST -H "Content-Type: text/xml" \
    -d '<?xml version="1.0"?><Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006"><Request><EMailAddress>test@bibop.com</EMailAddress></Request></Autodiscover>' \
    http://autodiscover.bibop.com/autodiscover/autodiscover.xml

# Test Thunderbird autoconfig
curl http://autoconfig.bibop.com/.well-known/autoconfig/mail/config-v1.1.xml
```

### Verificare DNS
```bash
dig autodiscover.dominio.com A +short
dig _autodiscover._tcp.dominio.com SRV +short
```

### Log errori
```bash
tail -f /var/log/autodiscover.log
sudo tail -f /var/log/nginx/error.log
```

---

## NOTE

- I record DNS devono essere configurati PRIMA di generare i certificati SSL
- Outlook prova prima HTTPS, poi HTTP - funziona anche senza SSL
- iOS/macOS usano principalmente i record SRV
- Thunderbird usa autoconfig.dominio.com

---

*Ultimo aggiornamento: 2026-01-15*
*Server: 80.240.31.197 (Vultr)*
