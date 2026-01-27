#!/bin/bash
# LORENZ Auto-Fix Script
# This script automatically finds the project, updates it, and fixes the database

set -e  # Exit on error

echo "=== LORENZ Automatic Fix Script ==="
echo ""

# Step 1: Find the project directory
echo "1. Searching for LORENZ project directory..."
PROJECT_DIR=$(find / -name "lorenz-backend" -type d 2>/dev/null | grep -v "docker" | head -1)

if [ -z "$PROJECT_DIR" ]; then
    echo "ERROR: Cannot find lorenz-backend directory on this server!"
    exit 1
fi

# Get the parent directory (project root)
PROJECT_ROOT=$(dirname "$PROJECT_DIR")
echo "   Found project at: $PROJECT_ROOT"
echo ""

# Step 2: Navigate to project and update code
echo "2. Updating code from repository..."
cd "$PROJECT_ROOT"

if [ ! -d ".git" ]; then
    echo "ERROR: $PROJECT_ROOT is not a git repository!"
    exit 1
fi

git fetch origin
git pull origin main
echo "   Code updated successfully"
echo ""

# Step 3: Install missing dependencies in container
echo "3. Installing psycopg2-binary in backend container..."
docker exec lorenz-backend pip install psycopg2-binary
echo "   Dependencies installed"
echo ""

# Step 4: Restart backend to load new code
echo "4. Restarting backend container..."
docker restart lorenz-backend
sleep 15
echo "   Backend restarted"
echo ""

# Step 5: Run database migrations
echo "5. Running database migrations..."
docker exec lorenz-backend alembic upgrade head
echo "   Migrations completed"
echo ""

# Step 6: Create admin user
echo "6. Creating admin user..."
docker exec lorenz-backend python3 scripts/create_admin_user.py
echo ""

# Step 7: Test login endpoint
echo "7. Testing login endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS")

echo "   Response: $BODY"
echo "   HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "=== ✅ SUCCESS! Login is working! ==="
    echo ""
    echo "Credentials:"
    echo "  URL: https://lorenz.bibop.com"
    echo "  Email: admin@lorenz.ai"
    echo "  Password: adminpassword123"
else
    echo "=== ❌ Login still failing with status $HTTP_STATUS ==="
    echo "Checking backend logs..."
    docker logs lorenz-backend --tail 20
fi
