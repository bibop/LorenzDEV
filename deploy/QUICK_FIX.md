# Quick Fix for Database Issue

## Problem Found
The database tables don't exist! Error: `relation "users" does not exist`

## Solution
Run these commands in your SSH terminal (you're already connected):

```bash
sudo su -
cd /root/lorenz
docker exec -it lorenz-backend alembic upgrade head
docker exec lorenz-backend python3 scripts/create_admin_user.py
```

## What This Does
1. Becomes root user
2. Goes to project directory
3. **Runs database migrations** (creates all tables)
4. **Creates admin user** with credentials

## After Running
Login should work with:
- Email: admin@lorenz.ai
- Password: adminpassword123
