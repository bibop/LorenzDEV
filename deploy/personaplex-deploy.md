# PersonaPlex Server Deployment Guide

## Overview

This guide covers deploying PersonaPlex speech-to-speech AI on a Vultr GPU instance for production use with LORENZ.

## Prerequisites

### 1. Vultr GPU Instance
- **Recommended**: Cloud GPU with NVIDIA A100 (40-80GB VRAM)
- **OS**: Ubuntu 22.04 LTS
- **Minimum specs**:
  - 8 CPU cores
  - 32GB RAM
  - 40GB GPU VRAM
  - 100GB SSD storage

### 2. Hugging Face Account
- Create account at https://huggingface.co
- Accept NVIDIA PersonaPlex license at https://huggingface.co/nvidia/personaplex-7b-v1
- Generate access token: Settings → Access Tokens → New token (Read)

### 3. Domain Setup
- Point `personaplex.lorenz.bibop.com` to server IP
- Configure DNS A record

## Deployment Steps

### Quick Deploy (Automated)

```bash
# 1. SSH into Vultr instance
ssh root@YOUR_SERVER_IP

# 2. Download and run setup script
curl -sSL https://raw.githubusercontent.com/yourusername/LorenzDEV/main/deploy/setup-personaplex.sh | sudo bash
```

When prompted, enter your Hugging Face token.

### Manual Deploy

#### 1. System Setup
```bash
# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3.10 python3-pip git curl nginx certbot \
    python3-certbot-nginx libopus-dev build-essential
```

#### 2. Install CUDA
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda-toolkit-12-3
```

#### 3. Clone and Setup PersonaPlex
```bash
cd /opt
git clone https://github.com/nvidia/personaplex.git
cd personaplex

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Download Model
```bash
export HF_TOKEN="your_huggingface_token_here"
python3 -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('nvidia/personaplex-7b-v1', token='$HF_TOKEN')"
```

#### 5. Configure SSL
```bash
mkdir -p /opt/personaplex/ssl

# Self-signed (development)
openssl req -x509 -newkey rsa:4096 -keyout /opt/personaplex/ssl/key.pem \
    -out /opt/personaplex/ssl/cert.pem -days 365 -nodes \
    -subj "/CN=personaplex.lorenz.bibop.com"

# Let's Encrypt (production)
certbot --nginx -d personaplex.lorenz.bibop.com
```

#### 6. Create Systemd Service
```bash
nano /etc/systemd/system/personaplex.service
```

Paste:
```ini
[Unit]
Description=PersonaPlex Voice Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/personaplex
Environment="HF_TOKEN=your_token_here"
Environment="SSL_DIR=/opt/personaplex/ssl"
ExecStart=/opt/personaplex/venv/bin/python -m moshi.server --ssl "$SSL_DIR"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable personaplex
systemctl start personaplex
systemctl status personaplex
```

#### 7. Configure Nginx
```bash
nano /etc/nginx/sites-available/personaplex
```

Paste:
```nginx
server {
    listen 443 ssl http2;
    server_name personaplex.lorenz.bibop.com;

    ssl_certificate /opt/personaplex/ssl/cert.pem;
    ssl_certificate_key /opt/personaplex/ssl/key.pem;

    location / {
        proxy_pass https://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}

server {
    listen 80;
    server_name personaplex.lorenz.bibop.com;
    return 301 https://$server_name$request_uri;
}
```

Enable:
```bash
ln -s /etc/nginx/sites-available/personaplex /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## Verification

### Check Service Status
```bash
systemctl status personaplex
journalctl -u personaplex -f
```

### Test API
```bash
curl https://personaplex.lorenz.bibop.com/health
```

Expected response: `{"status": "healthy"}`

### GPU Monitoring
```bash
watch -n 1 nvidia-smi
```

## Backend Configuration

Update LORENZ backend `.env`:
```env
PERSONAPLEX_URL=https://personaplex.lorenz.bibop.com
PERSONAPLEX_TIMEOUT=60
```

## Monitoring & Maintenance

### View Logs
```bash
# Real-time logs
journalctl -u personaplex -f

# Last 100 lines
journalctl -u personaplex -n 100

# Errors only
journalctl -u personaplex -p err
```

### Restart Service
```bash
systemctl restart personaplex
```

### Update PersonaPlex
```bash
cd /opt/personaplex
git pull
source venv/bin/activate
pip install --upgrade -r requirements.txt
systemctl restart personaplex
```

### GPU Health
```bash
# Temperature and usage
nvidia-smi

# Continuous monitoring
watch -n 1 nvidia-smi
```

## Cost Optimization

### On-Demand vs Reserved

| Type | Cost/Month | Best For |
|------|-----------|----------|
| On-Demand | ~$440 | Testing, variable usage |
| Reserved (1yr) | ~$300 | Production, constant usage |
| Serverless | Pay per call | Low usage, prototyping |

### Auto-Shutdown Script
Create `/opt/personaplex/auto-shutdown.sh`:
```bash
#!/bin/bash
# Shutdown if no activity for 1 hour
IDLE_TIME=3600

if [ $(systemctl is-active personaplex) == "active" ]; then
    LAST_LOG=$(journalctl -u personaplex -n 1 --since "1 hour ago" | wc -l)
    if [ $LAST_LOG -eq 0 ]; then
        echo "No activity, shutting down..."
        shutdown -h now
    fi
fi
```

Add to crontab:
```bash
crontab -e
# Add: */30 * * * * /opt/personaplex/auto-shutdown.sh
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
journalctl -u personaplex -n 50

# Common issues:
# 1. Wrong HF_TOKEN → Update /etc/systemd/system/personaplex.service
# 2. Out of memory → Reduce batch size or upgrade GPU
# 3. CUDA not found → Reinstall CUDA toolkit
```

### High Latency
- Check GPU memory: `nvidia-smi`
- Monitor network: `iftop`
- Optimize batch size in PersonaPlex config

### SSL Certificate Expired
```bash
certbot renew
systemctl reload nginx
```

## Security

### Firewall
```bash
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### API Key Authentication
Consider adding API key auth in Nginx:
```nginx
location / {
    if ($http_x_api_key != "your_secret_key") {
        return 401;
    }
    proxy_pass https://localhost:8080;
}
```

## Next Steps

1. ✅ Server deployed and running
2. Update LORENZ backend `.env`
3. Test voice upload via API
4. Create default voice library
5. Frontend voice UI integration
