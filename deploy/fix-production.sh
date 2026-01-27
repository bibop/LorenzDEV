#!/bin/bash
# Complete debug and fix script for LORENZ production

echo "=== LORENZ Production Debug & Fix Script ==="
echo ""

echo "1. Checking current Nginx configuration..."
echo "---"
cat /etc/nginx/sites-available/lorenz.bibop.com
echo ""
echo "---"

echo "2. Checking if configuration was updated..."
grep -n "proxy_pass http://localhost:8050;" /etc/nginx/sites-available/lorenz.bibop.com || echo "NOT FOUND - Configuration not updated!"
echo ""

echo "3. Updating Nginx configuration from Git..."
cp /root/lorenz/deploy/lorenz.bibop.com.conf /etc/nginx/sites-available/lorenz.bibop.com
echo "Configuration copied"
echo ""

echo "4. Verifying new configuration..."
grep -n "proxy_pass" /etc/nginx/sites-available/lorenz.bibop.com
echo ""

echo "5. Testing Nginx configuration..."
nginx -t
echo ""

echo "6. Reloading Nginx..."
systemctl reload nginx
echo "Nginx reloaded"
echo ""

echo "7. Checking Docker containers..."
docker ps | grep lorenz
echo ""

echo "8. Checking backend logs (last 20 lines)..."
docker logs lorenz-backend --tail 20
echo ""

echo "9. Testing backend health endpoint..."
curl -s http://localhost:8050/health | jq . || curl -s http://localhost:8050/health
echo ""

echo "10. Testing login endpoint directly on backend..."
curl -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\nHTTP Status: %{http_code}\n"
echo ""

echo "11. Testing login through Nginx..."
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}' \
  -w "\nHTTP Status: %{http_code}\n"
echo ""

echo "12. Checking Nginx error logs..."
tail -20 /var/log/nginx/lorenz_error.log
echo ""

echo "=== Debug Complete ==="
echo ""
echo "If login still fails, check:"
echo "- Backend container is running: docker ps | grep lorenz-backend"
echo "- Database connection: docker exec lorenz-backend python3 -c 'from app.database import engine; print(engine)'"
echo "- Admin user exists: docker exec lorenz-backend python3 scripts/create_admin_user.py"
