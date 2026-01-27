#!/bin/bash
# Run database migrations and create admin user

echo "Running database migrations..."
docker exec -it lorenz-backend alembic upgrade head

echo ""
echo "Creating admin user..."
docker exec lorenz-backend python3 scripts/create_admin_user.py

echo ""
echo "Done! Try logging in now."
