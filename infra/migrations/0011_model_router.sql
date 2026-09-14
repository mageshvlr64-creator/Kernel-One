-- 0011_model_router.sql — Model Router service tables (Character 1).
-- Forward-only; never edit after applied in any environment
-- (docs/schemas/01_database_schema.md migration policy).
--
-- `models` matches the canonical DDL in docs/schemas/01_database_schema.md
-- exactly. `model_audit_events` is the router-local audit stream; it will be
-- bridged into the canonical hash-chained `audit_events` by the audit-service
-- (Character 5, features/17_audit) — kept name-spaced here so we never write
-- to another character's canonical table directly.

-- Enum types may already exist if an earlier migration created them; guard
-- without rewriting history.
DO $$
BEGIN
    CREATE TYPE classification_level AS ENUM ('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS models (
    id                          text PRIMARY KEY,
    display_name                text NOT NULL,
    provider                    text NOT NULL CHECK (provider IN ('vllm','ollama','llamacpp')),
    total_parameters_billions   numeric NOT NULL,
    active_parameters_billions  numeric,
    quantization                text NOT NULL,
    context_window              integer NOT NULL,
    capabilities                text[] NOT NULL DEFAULT '{}',
    max_classification          classification_level NOT NULL DEFAULT 'INTERNAL',
    is_available                boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS model_audit_events (
    event_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "timestamp"     timestamptz NOT NULL DEFAULT now(),
    event_type      text NOT NULL,
    actor_id        text,
    model_id        text,
    provider        text,
    classification  classification_level,
    result          text NOT NULL CHECK (result IN ('success','error','fallback')),
    error_code      text,
    details         text
);
CREATE INDEX IF NOT EXISTS idx_model_audit_events_model
    ON model_audit_events (model_id, "timestamp" DESC);
CREATE INDEX IF NOT EXISTS idx_model_audit_events_correlation
    ON model_audit_events (event_type, "timestamp" DESC);

-- Audit-append safety: the router only ever inserts audit rows.
REVOKE UPDATE, DELETE ON model_audit_events FROM PUBLIC;
