#!/bin/bash
# LORENZ Quick Fix - No Git Required
# Run this on the server as linuxuser (with sudo)

echo "=== LORENZ Database Fix (Container-Only) ==="
echo ""

echo "1. Installing psycopg2-binary in backend container..."
sudo docker exec lorenz-backend pip install psycopg2-binary

echo ""
echo "2. Restarting backend container..."
sudo docker restart lorenz-backend

echo ""
echo "3. Waiting for backend to initialize (15 seconds)..."
sleep 15

echo ""
echo "4. Running database migrations..."
sudo docker exec lorenz-backend alembic upgrade head

echo ""
echo "5. Creating admin user..."
sudo docker exec lorenz-backend python3 scripts/create_admin_user.py

echo ""
echo "6. Testing login endpoint..."
curl -s -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\n\nHTTP STATUS: %{http_code}\n"

echo ""
echo "=== Done! Try logging in at https://lorenz.bibop.com ==="
echo "Email: admin@lorenz.ai"
echo "Password: adminpassword123"
