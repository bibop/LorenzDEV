# LORENZ Auto-Setup Discovery System

Sistema di setup automatizzato per nuovi utenti che scopre e collega automaticamente le fonti dati dell'utente.

## Architettura

```
discovery/
├── __init__.py           # Exports principali
├── local.py              # LocalDiscoveryService - scan file locali
├── cloud.py              # CloudStorageDiscovery - Google Drive, OneDrive, Dropbox
├── social.py             # SocialHistoryIngestion - LinkedIn, Twitter, Meta
├── orchestrator.py       # AutoSetupOrchestrator - coordina tutto
└── README.md
```

## Flusso di Setup

1. **Inizializzazione** (`POST /api/v1/onboarding/auto-setup/start`)
   - Quick scan del sistema locale
   - Crea piano personalizzato basato su cosa è disponibile
   - Ritorna lista step con priorità

2. **Esecuzione Step** (`POST /api/v1/onboarding/auto-setup/execute-step`)
   - Esegue uno step specifico
   - Per step OAuth, richiede token
   - Aggiorna progresso

3. **Completamento** (`POST /api/v1/onboarding/auto-setup/complete`)
   - Finalizza setup
   - Aggiorna stato utente

## Servizi

### LocalDiscoveryService

Scansiona il computer locale per trovare:
- Documenti (PDF, DOCX, ODT, etc.)
- Fogli di calcolo (XLSX, CSV)
- Presentazioni (PPTX, KEY)
- Note (TXT, MD)
- Archivi email (MBOX, PST, EML)
- Calendari (ICS)

```python
from app.services.discovery import LocalDiscoveryService

service = LocalDiscoveryService(
    max_file_size_mb=100,
    include_hidden=False,
    compute_hashes=False,
)

# Quick scan per vedere cosa c'è
summary = await service.quick_scan()

# Scan completo
result = await service.run_full_discovery()
print(f"Trovati {result.files_found} file")
```

### CloudStorageDiscovery

Scopre file da cloud storage dopo OAuth:
- Google Drive
- Microsoft OneDrive
- Dropbox

```python
from app.services.discovery import CloudStorageDiscovery
from app.services.discovery.cloud import CloudProvider

async with CloudStorageDiscovery(
    access_token="...",
    provider=CloudProvider.GOOGLE_DRIVE,
    max_results=500,
) as discovery:
    result = await discovery.discover_all()
    print(f"Trovati {result.files_found} file in Google Drive")
```

### SocialHistoryIngestion

Raccoglie la storia dell'utente dai social:
- LinkedIn (profilo, esperienze, competenze)
- Twitter/X (profilo, tweet, interessi)
- Facebook (profilo, post)
- Instagram (profilo, media)

```python
from app.services.discovery import SocialHistoryIngestion
from app.services.discovery.social import SocialPlatform

async with SocialHistoryIngestion(
    access_token="...",
    platform=SocialPlatform.LINKEDIN,
    max_posts=100,
) as ingestion:
    result = await ingestion.ingest()
    print(f"Profilo: {result.profile.name}")
    print(f"Esperienze: {len(result.experiences)}")
    print(f"Competenze: {result.skills}")
```

### AutoSetupOrchestrator

Coordina l'intero processo:

```python
from app.services.discovery import AutoSetupOrchestrator

orchestrator = AutoSetupOrchestrator(db, user_id, tenant_id)
progress = await orchestrator.initialize_setup()

# Esegui step
step = await orchestrator.execute_step("local_scan")

# Salta step
step = await orchestrator.skip_step("social_twitter")

# Prossimo step
next_step = orchestrator.get_next_step()
```

## API Endpoints

### Auto-Setup

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/onboarding/auto-setup/start` | POST | Inizia setup automatico |
| `/onboarding/auto-setup/progress` | GET | Stato corrente |
| `/onboarding/auto-setup/execute-step` | POST | Esegui step |
| `/onboarding/auto-setup/skip-step/{id}` | POST | Salta step |
| `/onboarding/auto-setup/complete` | POST | Completa setup |

### Discovery Diretta

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/onboarding/discovery/quick-scan` | GET | Quick scan sistema |
| `/onboarding/discovery/local-scan` | POST | Scan file locali |
| `/onboarding/discovery/cloud` | POST | Scan cloud storage |
| `/onboarding/discovery/social` | POST | Ingest social |

## Step di Setup

| ID | Fase | Priorità | OAuth |
|----|------|----------|-------|
| `local_scan` | DETECTING_LOCAL | Recommended | No |
| `email_google` | CONNECTING_EMAIL | Required | Google |
| `email_microsoft` | CONNECTING_EMAIL | Optional | Microsoft |
| `calendar_google` | CONNECTING_CALENDAR | Recommended | Google |
| `calendar_microsoft` | CONNECTING_CALENDAR | Optional | Microsoft |
| `cloud_google_drive` | DISCOVERING_CLOUD | Recommended | Google |
| `cloud_onedrive` | DISCOVERING_CLOUD | Optional | Microsoft |
| `cloud_dropbox` | DISCOVERING_CLOUD | Optional | Dropbox |
| `social_linkedin` | CONNECTING_SOCIAL | Recommended | LinkedIn |
| `social_twitter` | CONNECTING_SOCIAL | Optional | Twitter |
| `social_meta` | CONNECTING_SOCIAL | Optional | Meta |
| `index_documents` | INDEXING_DOCUMENTS | Recommended | No |
| `build_profile` | BUILDING_PROFILE | Required | No |

## Privacy

- **Tutti i dati rimangono sotto controllo dell'utente**
- L'utente può saltare qualsiasi step
- I file locali non vengono caricati automaticamente (solo metadati)
- L'utente sceglie quali documenti indicizzare
- I dati social servono solo per costruire il profilo Twin

## Integrazione Frontend

Il frontend dovrebbe:

1. Chiamare `POST /auto-setup/start` all'arrivo di un nuovo utente
2. Mostrare la lista degli step con stato
3. Per ogni step OAuth, aprire popup OAuth e poi chiamare `execute-step` con i token
4. Mostrare progresso in tempo reale
5. Permettere skip degli step opzionali
6. Chiamare `/auto-setup/complete` alla fine

## CLI Agent (Futuro)

Per la scansione locale completa, servirà un agent installato sul computer dell'utente:

```bash
# Installazione
pip install lorenz-agent

# Esecuzione
lorenz-agent discover --output discovery.json
lorenz-agent upload --file discovery.json --token USER_TOKEN
```
