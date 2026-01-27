#!/bin/bash
# Debug script for LORENZ production issues

echo "=== LORENZ Production Debug ==="
echo ""

echo "1. Checking Docker containers..."
docker ps -a | grep lorenz
echo ""

echo "2. Checking backend logs (last 50 lines)..."
docker logs lorenz-backend --tail 50
echo ""

echo "3. Checking frontend logs (last 50 lines)..."
docker logs lorenz-frontend --tail 50
echo ""

echo "4. Testing backend health endpoint..."
curl -s http://localhost:8050/health || echo "Backend health check failed"
echo ""

echo "5. Testing frontend..."
curl -I http://localhost:3050 || echo "Frontend check failed"
echo ""

echo "6. Checking Nginx status..."
systemctl status nginx | head -20
echo ""

echo "7. Testing Nginx proxy to backend..."
curl -s http://localhost/api/health || echo "Nginx proxy to backend failed"
echo ""

echo "8. Checking database connectivity..."
psql -h localhost -p 5433 -U lorenz -d lorenz -c "SELECT 1;" || echo "Database connection failed"
echo ""

echo "=== Debug Complete ==="
