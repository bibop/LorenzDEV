#!/bin/bash
# Fix database (Unified fix for 500 UndefinedTableError)

echo "=== LORENZ Database Fix (2026-01-27) ==="

echo "1. Installing missing dependencies in backend container..."
docker exec lorenz-backend pip install psycopg2-binary

echo "2. Restarting backend to trigger init_db (now with correct Base metadata)..."
docker restart lorenz-backend

echo "3. Waiting for backend to initialize (15s)..."
sleep 15

echo "4. Double-check: Running migrations explicitly..."
docker exec lorenz-backend alembic upgrade head

echo "5. Provisioning Admin User..."
docker exec lorenz-backend python3 scripts/create_admin_user.py

echo "6. Verifying Login Endpoint..."
curl -s -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\n\nHTTP STATUS: %{http_code}\n" | grep -A 1 "HTTP STATUS"

echo ""
echo "=== Fix Complete! Please try the browser now. ==="
