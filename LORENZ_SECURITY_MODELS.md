# 🔐 LORENZ Security & Compliance Models Setup

## 🎯 Modelli Uncensored per Security Testing

### 1. Dolphin Mixtral 8x7B Uncensored ⭐⭐⭐⭐⭐ (CONSIGLIATO)
```bash
ollama pull dolphin-mixtral:8x7b
```
**Specs:**
- Size: ~26GB
- RAM: 16GB+ (perfetto per il tuo server)
- Uncensored: ✅ Completamente
- Security: Eccellente per pentesting, exploit analysis, security research

**Capabilities:**
- ✅ Vulnerability analysis
- ✅ Exploit development assistance
- ✅ Code review per security
- ✅ Network penetration testing
- ✅ Malware analysis
- ✅ Social engineering scenarios

**Pro:**
- Nessun filtro etico su security topics
- Ottimo per CTF challenges
- Perfetto per red teaming
- Multilingua (ITA/ENG)

---

### 2. WizardLM Uncensored 13B ⭐⭐⭐⭐
```bash
ollama pull wizard-vicuna-uncensored:13b
```
**Specs:**
- Size: ~7.4GB
- RAM: 10GB+
- Uncensored: ✅
- Coding: Eccellente

**Use Case:**
- Exploit development
- Reverse engineering assistance
- Security code generation

---

### 3. Nous Hermes 2 Pro (Uncensored) ⭐⭐⭐⭐
```bash
ollama pull nous-hermes2-pro:latest
```
**Specs:**
- Size: ~7.5GB
- RAM: 10GB+
- Function calling: ✅
- Structured output: ✅

**Use Case:**
- Automated security scanning
- API exploitation
- Tool integration

---

## 📋 Modelli per NormaOS (Compliance Internazionale)

### 1. Mistral Nemo 12B ⭐⭐⭐⭐⭐ (BEST FOR COMPLIANCE)
```bash
ollama pull mistral-nemo:12b
```
**Specs:**
- Size: ~7GB
- RAM: 12-15GB
- Multilingua: ✅ Eccellente ITA/ENG
- Legal reasoning: ✅ Ottimo

**Capabilities:**
- ✅ Legal document analysis
- ✅ Compliance checking
- ✅ Regulatory interpretation
- ✅ Multi-jurisdictional knowledge
- ✅ Structured JSON output
- ✅ Contracts review

**Perfect for NormaOS:**
- GDPR compliance
- ISO standards
- International regulations
- Risk assessment
- Audit support

---

### 2. Qwen 2.5 14B (Compliance Alternative) ⭐⭐⭐⭐
```bash
ollama pull qwen2.5:14b
```
**Specs:**
- Size: ~9GB
- RAM: 14GB+
- Legal: Forte
- Multilingua: Eccellente

**Use Case:**
- Complex regulatory analysis
- International law
- Compliance reporting

---

## 🎯 Setup Raccomandato Finale

### Strategia Multi-Model per LORENZ

```python
LORENZ_SPECIALIZED_MODELS = {
    # WHITE HAT HACKING
    'security': {
        'pentesting': 'dolphin-mixtral:8x7b',     # Main uncensored
        'exploit_dev': 'wizard-vicuna-uncensored:13b',
        'api_hacking': 'nous-hermes2-pro'
    },
    
    # NORMAOS - COMPLIANCE
    'compliance': {
        'legal_analysis': 'mistral-nemo:12b',     # Main compliance
        'regulations': 'qwen2.5:14b',
        'contracts': 'mistral-nemo:12b'
    },
    
    # GENERAL PURPOSE
    'general': {
        'reasoning': 'deepseek-r1:14b',           # Già installato
        'chat': 'mistral-nemo:12b',
        'vision': 'llava:7b',                     # Già installato
        'quick': 'deepseek-r1:1.5b'               # Già installato
    }
}
```

---

## 📦 Piano di Installazione

### Step 1: Cleanup Modelli Non Necessari
```bash
# Rimuovi modelli che non servono
ollama rm deepseek-r1:32b        # 19GB (troppo grande)
ollama rm openai-hacker          # 11GB (sostituito da Dolphin)
ollama rm llama-moe-hacker       # 6.1GB (sostituito da Wizard)
ollama rm qwen3-thinker          # 7.8GB (sostituito da Qwen2.5)

# Spazio liberato: ~44GB
```

### Step 2: Install Security Models
```bash
# Uncensored per security
ollama pull dolphin-mixtral:8x7b              # 26GB
ollama pull wizard-vicuna-uncensored:13b      # 7.4GB
ollama pull nous-hermes2-pro                  # 7.5GB
```

### Step 3: Install Compliance Models
```bash
# Per NormaOS
ollama pull mistral-nemo:12b                  # 7GB
ollama pull qwen2.5:14b                       # 9GB
```

### Riepilogo Finale:
```
Modelli Installati Totali:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY (Uncensored):
├── dolphin-mixtral:8x7b          26GB  ⭐ Main
├── wizard-vicuna-uncensored:13b   7.4GB
└── nous-hermes2-pro               7.5GB

COMPLIANCE (NormaOS):
├── mistral-nemo:12b               7GB   ⭐ Main
└── qwen2.5:14b                    9GB

GENERAL PURPOSE:
├── deepseek-r1:14b                9GB   (existing)
├── llava:7b                       4.7GB (existing)
└── deepseek-r1:1.5b               1.1GB (existing)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: ~79GB
Disk Available: 73GB → Need ~6GB more space
```

---

## ⚠️ Problema Spazio

Con 73GB disponibili e 79GB necessari, serve liberare altro spazio O scegliere subset.

### Opzione A: Setup Minimo (Recommended)
```bash
# Solo i modelli principali
ollama rm deepseek-r1:32b openai-hacker llama-moe-hacker qwen3-thinker
ollama pull dolphin-mixtral:8x7b    # Security uncensored
ollama pull mistral-nemo:12b        # Compliance + Chat

# Total: ~47GB
# Perfettamente nei limiti!
```

### Opzione B: Setup Completo (Requires cleanup)
Elimina altri file dal server per liberare ~10GB extra.

---

## 🔐 Security Notes

### Dolphin Mixtral - Security Capabilities

**Uncensored Topics:**
- ✅ Vulnerability research
- ✅ Exploit development
- ✅ Penetration testing
- ✅ Social engineering
- ✅ Malware analysis
- ✅ Network attacks
- ✅ Cryptography breaking
- ✅ Zero-day research

**Legal Use Only:**
⚠️ Use for authorized security testing only
⚠️ White hat hacking / ethical pentesting
⚠️ CTF competitions
⚠️ Security research
⚠️ Defensive security

---

## 📋 NormaOS Integration

### API Endpoints for Compliance

```python
# NormaOS Compliance Engine
class NormaOSCompliance:
    def __init__(self):
        self.model = 'mistral-nemo:12b'
        
    async def check_compliance(self, document, jurisdiction):
        """Check document compliance with regulations"""
        prompt = f"""
        Analyze this document for compliance with {jurisdiction} regulations:
        
        Document:
        {document}
        
        Check for:
        - GDPR compliance
        - Data protection
        - Privacy policies
        - Legal requirements
        - Risk factors
        
        Return structured JSON with compliance score and issues.
        """
        return await ollama.generate(self.model, prompt)
        
    async def generate_compliance_report(self, company_data):
        """Generate compliance audit report"""
        # International regulations
        # ISO standards
        # Industry-specific rules
```

---

## 🎯 Conclusione

**Setup Raccomandato Immediato:**

1. **Dolphin Mixtral 8x7b** → White hat hacking (uncensored)
2. **Mistral Nemo 12B** → NormaOS compliance + general chat
3. **Keep existing**: DeepSeek R1 14B, Llava 7B, DeepSeek 1.5B

**Benefici:**
- ✅ Uncensored per security research
- ✅ Compliance internazionale forte
- ✅ Multilingua perfetto
- ✅ Dentro limiti RAM (16GB)
- ✅ Dentro limiti disk

