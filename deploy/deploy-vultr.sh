#!/bin/bash
# LORENZ - Vultr Deployment Script
# Usage: ./deploy-vultr.sh [IP_ADDRESS]

set -e

# Configuration
VULTR_IP="${1:-80.240.31.197}"
SSH_USER="linuxuser"
DEPLOY_DIR="/opt/lorenz"

echo "🚀 Deploying LORENZ to Vultr server: $VULTR_IP"

# Step 1: Prepare server
echo "📦 Preparing server and installing Docker..."
ssh $SSH_USER@$VULTR_IP << 'ENDSSH'
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        sudo curl -fsSL https://get.docker.com | sudo sh
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker $USER
    fi
    
    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Create deploy directory
    sudo mkdir -p /opt/lorenz/deploy/ssl
    sudo chown -R $USER:$USER /opt/lorenz
ENDSSH

# Step 2: Copy files (excluding heavy dirs that Docker will rebuild)
echo "📁 Copying project files..."
rsync -avz --exclude='node_modules' --exclude='.next' --exclude='__pycache__' \
    --exclude='.git' --exclude='.env' --exclude='*.pyc' --exclude='venv' \
    --exclude='*.egg-info' --exclude='.pytest_cache' \
    ./ $SSH_USER@$VULTR_IP:$DEPLOY_DIR/

# Step 3: Copy environment file
echo "🔐 Copying environment configuration..."
if [ -f ".env.production" ]; then
    scp .env.production $SSH_USER@$VULTR_IP:$DEPLOY_DIR/.env
else
    echo "⚠️  Warning: .env.production not found. Create it with your production secrets."
fi

# Step 4: Build and start
echo "🔨 Building and starting containers..."
ssh $SSH_USER@$VULTR_IP << ENDSSH
    cd $DEPLOY_DIR
    
    # Stop existing containers
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build fresh
    docker compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    docker compose -f docker-compose.prod.yml up -d
    
    # Show status
    echo "📊 Container status:"
    docker compose -f docker-compose.prod.yml ps
ENDSSH

# Step 5: Setup SSL certificates (run after DNS propagation)
echo "🔒 Attempting SSL certificate setup..."
ssh $SSH_USER@$VULTR_IP << 'ENDSSH'
    cd /opt/lorenz
    
    # Create webroot directory
    mkdir -p /opt/lorenz/certbot-webroot
    
    # Run certbot for SSL
    docker run --rm \
        -v /opt/lorenz/deploy/ssl:/etc/letsencrypt \
        -v /opt/lorenz/certbot-webroot:/var/www/certbot \
        certbot/certbot certonly --webroot \
        -w /var/www/certbot \
        -d lorenz.bibop.com \
        -d dev.lorenz.bibop.com \
        --email admin@bibop.com \
        --agree-tos \
        --non-interactive || echo "⚠️ SSL setup skipped - run manually after DNS propagation"
    
    # Restart nginx to load certs
    docker compose -f docker-compose.prod.yml restart nginx 2>/dev/null || true
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 URLs (after DNS propagation ~5 min):"
echo "   Production: https://lorenz.bibop.com"
echo "   Development: https://dev.lorenz.bibop.com"
echo ""
echo "📋 DNS Status: Already configured on GoDaddy"
echo "   lorenz.bibop.com     -> $VULTR_IP"
echo "   dev.lorenz.bibop.com -> $VULTR_IP"
