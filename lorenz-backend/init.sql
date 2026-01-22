-- LORENZ SaaS - Database Initialization
-- Run this when setting up a new PostgreSQL database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create RLS helper function
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Note: Tables are created by SQLAlchemy/Alembic
-- This file is for extensions and RLS setup

-- RLS Policies (applied after tables are created)
-- These will be added via Alembic migrations:

-- Example RLS policy for users table:
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY users_tenant_isolation ON users
--     USING (tenant_id = current_tenant_id());

-- Example for email_accounts:
-- ALTER TABLE email_accounts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY email_accounts_user_isolation ON email_accounts
--     USING (user_id IN (SELECT id FROM users WHERE tenant_id = current_tenant_id()));
