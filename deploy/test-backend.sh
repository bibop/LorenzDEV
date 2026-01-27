#!/bin/bash
# Simple test script - run this on the Vultr server

echo "Testing LORENZ backend..."
echo ""

# Test 1: Check if backend is running
echo "1. Backend container status:"
docker ps | grep lorenz-backend
echo ""

# Test 2: Test health endpoint
echo "2. Health check:"
curl -s http://localhost:8050/health
echo ""
echo ""

# Test 3: Test login endpoint
echo "3. Login test:"
curl -v -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  2>&1 | head -50
echo ""

# Test 4: Check backend logs
echo "4. Backend logs (last 10 lines):"
docker logs lorenz-backend --tail 10
echo ""

# Test 5: Check if admin user exists
echo "5. Creating/updating admin user:"
docker exec lorenz-backend python3 scripts/create_admin_user.py
