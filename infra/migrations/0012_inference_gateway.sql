-- 0012_inference_gateway.sql — Inference Gateway audit table (Character 1).
-- Forward-only; never edit after applied in any environment
-- (docs/schemas/01_database_schema.md migration policy).
--
-- The gateway's own audit stream for inference calls. Bridged into the
-- canonical hash-chained `audit_events` by the audit-service (Character 5,
-- features/17_audit) — name-spaced here so we never write to another
-- character's canonical table directly.

CREATE TABLE IF NOT EXISTS inference_audit_events (
    event_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "timestamp"     timestamptz NOT NULL DEFAULT now(),
    event_type      text NOT NULL DEFAULT 'inference_call',
    actor_id        text,
    model_id        text,
    provider        text,
    classification  classification_level,
    result          text NOT NULL CHECK (result IN ('success','error','fallback')),
    error_code      text,
    details         text,
    latency_ms      real
);
CREATE INDEX IF NOT EXISTS idx_inference_audit_events_model
    ON inference_audit_events (model_id, "timestamp" DESC);

-- Audit-append safety: the gateway only ever inserts audit rows.
REVOKE UPDATE, DELETE ON inference_audit_events FROM PUBLIC;
