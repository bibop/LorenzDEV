# LORENZ Production - Manual Fix Instructions

## Current Status
✅ **Confirmed**: Login returns 500 error (database tables missing)  
✅ **Code fix**: Already pushed to repository  
✅ **Scripts ready**: All fix scripts are ready

## The Issue
The server is missing:
1. The `psycopg2-binary` Python package (for migrations)
2. Database tables (need to run migrations)
3. Admin user (need to create it)

## Quick Fix (Copy-Paste This)

SSH into the server and run this **single command**:

```bash
curl -sSL https://raw.githubusercontent.com/bibop/LorenzDEV/main/deploy/auto-fix.sh | sudo bash
```

**OR** if the repo is private, run these commands:

```bash
# Step 1: Find the project
PROJECT=$(find / -name "lorenz-backend" -type d 2>/dev/null | grep -v docker | head -1)
PROJECT_ROOT=$(dirname "$PROJECT")

# Step 2: Go there and update
cd "$PROJECT_ROOT"
git pull origin main

# Step 3: Run the fix script
bash deploy/auto-fix.sh
```

## What The Script Does
1. Finds the project directory automatically
2. Updates code from Git
3. Installs `psycopg2-binary` in the backend container
4. Restarts the backend
5. Runs database migrations (creates tables)
6. Creates admin user
7. Tests the login endpoint

## Expected Output
At the end you should see:
```
✅ SUCCESS! Login is working!

Credentials:
  URL: https://lorenz.bibop.com
  Email: admin@lorenz.ai
  Password: adminpassword123
```

## If It Still Fails
Check:
1. Backend logs: `docker logs lorenz-backend --tail 50`
2. Database connection: `docker exec lorenz-backend python3 -c "from app.database import engine; print('OK')"`
3. Tables exist: Check if `users` table was created

## Credentials
- **URL**: https://lorenz.bibop.com
- **Email**: admin@lorenz.ai  
- **Password**: adminpassword123
