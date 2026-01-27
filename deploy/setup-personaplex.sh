#!/bin/bash
# PersonaPlex Server Deployment Script for Vultr GPU
# Run this on a fresh Vultr GPU instance (A100 recommended)

set -e  # Exit on error

echo "=== LORENZ PersonaPlex Server Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# System info
echo "System Information:"
nvidia-smi || echo "WARNING: No NVIDIA GPU detected!"
echo ""

# Update system
echo "1. Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "2. Installing dependencies..."
apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    curl \
    nginx \
    certbot \
    python3-certbot-nginx \
    libopus-dev \
    build-essential

# Install CUDA if not present
if ! command -v nvcc &> /dev/null; then
    echo "3. Installing CUDA toolkit..."
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
    dpkg -i cuda-keyring_1.0-1_all.deb
    apt-get update
    apt-get -y install cuda-toolkit-12-3
fi

# Clone PersonaPlex repository
echo "4. Cloning PersonaPlex repository..."
cd /opt
if [ -d "personaplex" ]; then
    echo "PersonaPlex already cloned, updating..."
    cd personaplex
    git pull
else
    git clone https://github.com/nvidia/personaplex.git
    cd personaplex
fi

# Create Python virtual environment
echo "5. Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "6. Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install httpx fastapi uvicorn python-multipart

# Set Hugging Face token
echo "7. Configuring Hugging Face access..."
read -p "Enter your Hugging Face token: " HF_TOKEN
export HF_TOKEN="$HF_TOKEN"
echo "export HF_TOKEN=\"$HF_TOKEN\"" >> ~/.bashrc

# Download PersonaPlex model
echo "8. Downloading PersonaPlex model (this may take a while)..."
python3 -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('nvidia/personaplex-7b-v1', token='$HF_TOKEN')"

# Create SSL directory
echo "9. Setting up SSL certificates..."
mkdir -p /opt/personaplex/ssl
SSL_DIR="/opt/personaplex/ssl"

# Generate self-signed certificate (replace with Let's Encrypt in production)
openssl req -x509 -newkey rsa:4096 -keyout $SSL_DIR/key.pem -out $SSL_DIR/cert.pem -days 365 -nodes -subj "/CN=personaplex.lorenz.bibop.com"

# Create systemd service
echo "10. Creating systemd service..."
cat > /etc/systemd/system/personaplex.service <<EOF
[Unit]
Description=PersonaPlex Voice Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/personaplex
Environment="HF_TOKEN=$HF_TOKEN"
Environment="SSL_DIR=/opt/personaplex/ssl"
ExecStart=/opt/personaplex/venv/bin/python -m moshi.server --ssl "\$SSL_DIR"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable personaplex
systemctl start personaplex

# Configure Nginx reverse proxy
echo "11. Configuring Nginx..."
cat > /etc/nginx/sites-available/personaplex <<EOF
server {
    listen 443 ssl http2;
    server_name personaplex.lorenz.bibop.com;

    ssl_certificate /opt/personaplex/ssl/cert.pem;
    ssl_certificate_key /opt/personaplex/ssl/key.pem;

    location / {
        proxy_pass https://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket settings
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}

server {
    listen 80;
    server_name personaplex.lorenz.bibop.com;
    return 301 https://\$server_name\$request_uri;
}
EOF

ln -sf /etc/nginx/sites-available/personaplex /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Configure firewall
echo "12. Configuring firewall..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw --force enable

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "PersonaPlex server is running on:"
echo "  - Local: https://localhost:8080"
echo "  - Public: https://personaplex.lorenz.bibop.com"
echo ""
echo "Check status: systemctl status personaplex"
echo "View logs: journalctl -u personaplex -f"
echo ""
echo "Next steps:"
echo "1. Point DNS personaplex.lorenz.bibop.com to this server IP"
echo "2. Replace self-signed cert with Let's Encrypt:"
echo "   certbot --nginx -d personaplex.lorenz.bibop.com"
echo "3. Update LORENZ backend .env with PERSONAPLEX_URL"
echo ""
