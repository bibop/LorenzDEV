#!/bin/bash
# Deploy script for LORENZ production fixes

set -e  # Exit on error

echo "=== LORENZ Production Deployment ==="
echo ""

echo "Step 1: Checking Docker containers status..."
docker ps | grep lorenz || echo "No lorenz containers found"
echo ""

echo "Step 2: Checking backend logs for errors..."
docker logs lorenz-backend --tail 20 2>&1 || echo "Cannot read backend logs"
echo ""

echo "Step 3: Testing login endpoint..."
curl -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  2>&1 || echo "Login test failed"
echo ""

echo "Step 4: Testing health endpoint..."
curl -s http://localhost:8050/health || echo "Health check failed"
echo ""

echo "Step 5: Checking Nginx status..."
systemctl status nginx | head -10
echo ""

echo "=== Deployment Verification Complete ==="
