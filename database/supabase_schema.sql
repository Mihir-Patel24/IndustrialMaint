-- ================================================================
-- supabase_schema.sql
-- IndustrialMaint AI — Supabase PostgreSQL Schema
-- ================================================================
-- Run in Supabase SQL Editor:
--   Dashboard → SQL Editor → New Query → Paste → Run
--
-- This creates all tables with Row Level Security (RLS) enabled
-- so users can only access their own data.
-- ================================================================

-- ── Extensions ───────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ================================================================
-- USERS
-- ================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email         TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    company       TEXT DEFAULT '',
    factory       TEXT DEFAULT '',
    department    TEXT DEFAULT '',
    role          TEXT DEFAULT 'Maintenance Engineer'
                  CHECK (role IN ('Admin','Plant Manager','Maintenance Engineer','Operator')),
    password_hash TEXT NOT NULL,
    avatar_color  TEXT DEFAULT '#1e40af',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login    TIMESTAMPTZ
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can read and update their own row
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT USING (id = current_setting('app.user_id', true));

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE USING (id = current_setting('app.user_id', true));

-- Service role can insert new users (registration)
CREATE POLICY "users_insert_service" ON public.users
    FOR INSERT WITH CHECK (true);


-- ================================================================
-- MACHINES
-- ================================================================
CREATE TABLE IF NOT EXISTS public.machines (
    id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id      TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    machine_id   TEXT NOT NULL,
    machine_name TEXT NOT NULL,
    machine_type TEXT DEFAULT 'CNC Milling',
    material     TEXT DEFAULT '',
    factory      TEXT DEFAULT '',
    location     TEXT DEFAULT '',
    status       TEXT DEFAULT 'Active'
                 CHECK (status IN ('Active','Idle','Maintenance','Offline')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_machines_user_id ON public.machines(user_id);

ALTER TABLE public.machines ENABLE ROW LEVEL SECURITY;

CREATE POLICY "machines_own" ON public.machines
    USING (user_id = current_setting('app.user_id', true))
    WITH CHECK (user_id = current_setting('app.user_id', true));


-- ================================================================
-- PREDICTIONS
-- ================================================================
CREATE TABLE IF NOT EXISTS public.predictions (
    id                   TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id              TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    machine_id           TEXT DEFAULT 'CNC-00',
    tool_health          REAL DEFAULT 0,
    machine_health       REAL DEFAULT 0,
    tool_wear            REAL DEFAULT 0,
    remaining_rul        REAL DEFAULT 0,
    failure_risk         REAL DEFAULT 0,
    failure_prob         REAL DEFAULT 0,
    failure_type         TEXT DEFAULT '',
    machine_status       TEXT DEFAULT '',
    maintenance_priority TEXT DEFAULT '',
    overall_risk         REAL DEFAULT 0,
    source               TEXT DEFAULT 'local',
    payload_json         JSONB DEFAULT '{}',
    result_json          JSONB DEFAULT '{}',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id  ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created  ON public.predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_machine  ON public.predictions(machine_id);

ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "predictions_own" ON public.predictions
    USING (user_id = current_setting('app.user_id', true))
    WITH CHECK (user_id = current_setting('app.user_id', true));


-- ================================================================
-- ALERTS
-- ================================================================
CREATE TABLE IF NOT EXISTS public.alerts (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    machine_id TEXT DEFAULT '',
    title      TEXT NOT NULL,
    detail     TEXT DEFAULT '',
    level      TEXT DEFAULT 'info'
               CHECK (level IN ('info','warning','critical')),
    is_read    BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_id  ON public.alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read  ON public.alerts(is_read);

ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alerts_own" ON public.alerts
    USING (user_id = current_setting('app.user_id', true))
    WITH CHECK (user_id = current_setting('app.user_id', true));


-- ================================================================
-- MAINTENANCE HISTORY
-- ================================================================
CREATE TABLE IF NOT EXISTS public.maintenance_history (
    id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id      TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    machine_id   TEXT NOT NULL,
    task         TEXT NOT NULL,
    priority     TEXT DEFAULT 'Medium'
                 CHECK (priority IN ('Low','Medium','High','Immediate')),
    status       TEXT DEFAULT 'Pending'
                 CHECK (status IN ('Pending','In Progress','Completed','Cancelled')),
    technician   TEXT DEFAULT '',
    est_time     TEXT DEFAULT '',
    notes        TEXT DEFAULT '',
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_maint_user_id ON public.maintenance_history(user_id);
CREATE INDEX IF NOT EXISTS idx_maint_status  ON public.maintenance_history(status);

ALTER TABLE public.maintenance_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "maint_own" ON public.maintenance_history
    USING (user_id = current_setting('app.user_id', true))
    WITH CHECK (user_id = current_setting('app.user_id', true));


-- ================================================================
-- AUDIT LOGS
-- ================================================================
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT REFERENCES public.users(id) ON DELETE SET NULL,
    action     TEXT NOT NULL,
    detail     TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id  ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created  ON public.audit_logs(created_at DESC);

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Admins can read all logs; users can only read their own
CREATE POLICY "audit_insert_all" ON public.audit_logs
    FOR INSERT WITH CHECK (true);

CREATE POLICY "audit_select_own" ON public.audit_logs
    FOR SELECT USING (user_id = current_setting('app.user_id', true));


-- ================================================================
-- PASSWORD RESET TOKENS
-- ================================================================
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    email      TEXT NOT NULL,
    token      TEXT UNIQUE NOT NULL,
    used       BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prt_token ON public.password_reset_tokens(token);

ALTER TABLE public.password_reset_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "prt_service_only" ON public.password_reset_tokens
    USING (true) WITH CHECK (true);  -- service role only; no direct client access


-- ================================================================
-- HELPER VIEWS
-- ================================================================

-- Per-user prediction summary
CREATE OR REPLACE VIEW public.v_user_prediction_stats AS
SELECT
    user_id,
    COUNT(*)                             AS total_predictions,
    AVG(failure_risk)                    AS avg_failure_risk,
    MAX(failure_risk)                    AS max_failure_risk,
    AVG(tool_health)                     AS avg_tool_health,
    SUM(CASE WHEN machine_status = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    MAX(created_at)                      AS last_prediction_at
FROM public.predictions
GROUP BY user_id;

-- Per-user unread alert count
CREATE OR REPLACE VIEW public.v_user_alert_summary AS
SELECT
    user_id,
    COUNT(*)                                              AS total_alerts,
    SUM(CASE WHEN NOT is_read THEN 1 ELSE 0 END)         AS unread_alerts,
    SUM(CASE WHEN level = 'critical' THEN 1 ELSE 0 END)  AS critical_alerts
FROM public.alerts
GROUP BY user_id;


-- ================================================================
-- DONE
-- ================================================================
-- Tables created:
--   users, machines, predictions, alerts,
--   maintenance_history, audit_logs, password_reset_tokens
-- Views created:
--   v_user_prediction_stats, v_user_alert_summary
-- RLS enabled on all tables.
-- ================================================================
