# LORENZ Production - Database Fix Instructions

## Problem
Database tables don't exist. Error: `relation "users" does not exist`

## Root Cause
The `init_db()` function in `app/database.py` creates tables on startup, but it didn't execute properly when the backend first started.

## Solution
Restart the backend container to trigger `init_db()` again, then create the admin user.

## Commands to Execute

Connect to the server and run:

```bash
sudo su -
cd /root/lorenz
git pull
bash deploy/restart-and-fix.sh
```

Or manually:

```bash
sudo su -
cd /root/lorenz
docker restart lorenz-backend
sleep 10
docker logs lorenz-backend --tail 15
docker exec lorenz-backend python3 scripts/create_admin_user.py
```

## After Running

Login credentials:
- URL: https://lorenz.bibop.com
- Email: admin@lorenz.ai
- Password: adminpassword123

## Verification

Test the login endpoint:
```bash
curl -X POST https://lorenz.bibop.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lorenz.ai","password":"adminpassword123"}'
```

Should return a token instead of "Internal server error".
