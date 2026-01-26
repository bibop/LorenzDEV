-- LORENZ - Row Level Security Policies
-- Multi-tenant data isolation

-- Enable RLS on all tenant-scoped tables
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see data from their own tenant
CREATE POLICY tenant_isolation_skills ON skills
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY tenant_isolation_skill_proposals ON skill_proposals
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY tenant_isolation_skill_runs ON skill_runs
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY tenant_isolation_rag_documents ON rag_documents
    USING (user_id IN (
        SELECT id FROM users WHERE tenant_id::text = current_setting('app.current_tenant_id', true)
    ));

CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY tenant_isolation_conversations ON conversations
    USING (user_id IN (
        SELECT id FROM users WHERE tenant_id::text = current_setting('app.current_tenant_id', true)
    ));

CREATE POLICY tenant_isolation_messages ON messages
    USING (conversation_id IN (
        SELECT id FROM conversations WHERE user_id IN (
            SELECT id FROM users WHERE tenant_id::text = current_setting('app.current_tenant_id', true)
        )
    ));

-- Grant usage permissions (service role bypasses RLS, authenticated uses it)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
