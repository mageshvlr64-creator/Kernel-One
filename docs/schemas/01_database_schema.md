# Database Schema (Canonical DDL)

> **Canonical owner** of the literal database schema. PostgreSQL 15+ (`06_TECHNOLOGY_STACK.md`
> DEC-002), `pgvector` extension required. This is the source of truth; `docs/domain/` is the
> conceptual view of the same tables.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE classification_level AS ENUM ('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED');
CREATE TYPE user_role AS ENUM ('Administrator','SecurityOfficer','Operator','Analyst','RestrictedUser','Auditor');
CREATE TYPE task_state AS ENUM ('CREATED','PLANNING','WAITING_APPROVAL','EXECUTING','WAITING_INPUT','COMPLETED','FAILED','CANCELLED');
CREATE TYPE tool_invocation_state AS ENUM ('CREATED','AUTHORIZED','RUNNING','SUCCEEDED','FAILED','TIMEOUT','CANCELLED');
CREATE TYPE approval_state AS ENUM ('REQUESTED','APPROVED','REJECTED','EXPIRED','CANCELLED');
CREATE TYPE artifact_state AS ENUM ('CREATED','VALIDATING','READY','APPROVED','REJECTED','EXPORTED','DELETED','FAILED');
CREATE TYPE document_state AS ENUM ('UPLOADED','VALIDATING','EXTRACTING','OCR','INDEXING','READY','FAILED','DELETED');

CREATE TABLE organizations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL UNIQUE,
    network_mode    text NOT NULL DEFAULT 'air_gapped'
                        CHECK (network_mode IN ('air_gapped','restricted','on_premise')),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workspaces (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id         uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name                    text NOT NULL,
    default_classification  classification_level NOT NULL DEFAULT 'INTERNAL',
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    deleted_at              timestamptz,
    UNIQUE (organization_id, name)
);

CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    username        text NOT NULL UNIQUE,
    display_name    text NOT NULL,
    password_hash   text NOT NULL,
    role            user_role NOT NULL,
    clearance       classification_level NOT NULL DEFAULT 'INTERNAL',
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    last_login_at   timestamptz
);
CREATE INDEX idx_users_org ON users(organization_id);

CREATE TABLE models (
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

CREATE TABLE documents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    filename        text NOT NULL,
    mime_type       text NOT NULL,
    size_bytes      bigint NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 209715200),
    sha256          char(64) NOT NULL,
    storage_uri     text NOT NULL,
    classification  classification_level NOT NULL DEFAULT 'INTERNAL',
    state           document_state NOT NULL DEFAULT 'UPLOADED',
    version         integer NOT NULL DEFAULT 1,
    uploaded_by     uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz
);
CREATE INDEX idx_documents_workspace ON documents(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_sha256 ON documents(sha256);

CREATE TABLE document_chunks (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     integer NOT NULL,
    page_number     integer,
    bbox            jsonb,
    text            text NOT NULL,
    embedding       vector(768) NOT NULL,
    ocr_confidence  real CHECK (ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 1)),
    text_search     tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_text_search ON document_chunks USING gin (text_search);

CREATE TABLE conversations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content         jsonb NOT NULL,
    model_id        text REFERENCES models(id),
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

CREATE TABLE tasks (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    conversation_id     uuid NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
    created_by          uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title               text NOT NULL,
    state               task_state NOT NULL DEFAULT 'CREATED',
    classification      classification_level NOT NULL DEFAULT 'INTERNAL',
    created_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz
);
CREATE INDEX idx_tasks_workspace_state ON tasks(workspace_id, state);

CREATE TABLE agent_runs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    plan            jsonb NOT NULL,
    model_id        text NOT NULL REFERENCES models(id),
    step_count      integer NOT NULL DEFAULT 0,
    replan_count    integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tool_invocations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_run_id    uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_id         text NOT NULL,
    state           tool_invocation_state NOT NULL DEFAULT 'CREATED',
    input           jsonb NOT NULL,
    output          jsonb,
    error_code      text,
    started_at      timestamptz,
    finished_at     timestamptz
);
CREATE INDEX idx_tool_invocations_task ON tool_invocations(task_id);

CREATE TABLE evidence (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    source_document_id  uuid NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    document_version    integer NOT NULL,
    chunk_id            uuid NOT NULL REFERENCES document_chunks(id) ON DELETE RESTRICT,
    page_number         integer,
    source_hash         char(64) NOT NULL,
    retrieval_method    text NOT NULL CHECK (retrieval_method IN ('vector','keyword','hybrid')),
    confidence          real,
    created_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_evidence_task ON evidence(task_id);

CREATE TABLE artifacts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    type                text NOT NULL CHECK (type IN ('docx','pptx','xlsx','pdf','csv','json','markdown','code')),
    filename            text NOT NULL,
    storage_uri         text NOT NULL,
    checksum            char(64) NOT NULL,
    classification      classification_level NOT NULL,
    state               artifact_state NOT NULL DEFAULT 'CREATED',
    generator_version   text NOT NULL,
    evidence_ids        uuid[] NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_artifacts_task ON artifacts(task_id);

CREATE TABLE approvals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action_type     text NOT NULL,
    action_ref_id   uuid NOT NULL,
    requested_by    uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    state           approval_state NOT NULL DEFAULT 'REQUESTED',
    decided_by      uuid REFERENCES users(id),
    decided_at      timestamptz,
    expires_at      timestamptz NOT NULL,
    reason          text
);
CREATE INDEX idx_approvals_task ON approvals(task_id);

CREATE TABLE policies (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL UNIQUE,
    scope           text NOT NULL CHECK (scope IN ('model','tool','document','network','export','approval')),
    rule            jsonb NOT NULL,
    priority        integer NOT NULL DEFAULT 100,
    created_by      uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- Audit: append-only, no UPDATE/DELETE grants on this table for any application role.
CREATE TABLE audit_events (
    event_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "timestamp"      timestamptz NOT NULL DEFAULT now(),
    event_type       text NOT NULL,
    actor_id         uuid NOT NULL,
    session_id       uuid,
    correlation_id   uuid,
    task_id          uuid,
    action           text NOT NULL CHECK (action IN ('create','read','update','delete','execute','approve','reject','export','login','logout')),
    resource_type    text NOT NULL,
    resource_id      uuid,
    classification   classification_level,
    decision         text CHECK (decision IN ('allowed','denied')),
    result           text NOT NULL CHECK (result IN ('success','error','denied')),
    error_code       text,
    reason           text,
    tool_id          text,
    model_id         text,
    artifact_id      uuid,
    source_interface text,
    source_ip        inet,
    payload_hash     char(64),
    prev_event_hash  char(64) NOT NULL
);
CREATE INDEX idx_audit_events_correlation ON audit_events(correlation_id);
CREATE INDEX idx_audit_events_actor ON audit_events(actor_id, "timestamp");
REVOKE UPDATE, DELETE ON audit_events FROM PUBLIC;

CREATE TABLE memory_entries (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope       text NOT NULL CHECK (scope IN ('conversation','task','workspace')),
    scope_id    uuid NOT NULL,
    content     text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    expires_at  timestamptz
);
CREATE INDEX idx_memory_scope ON memory_entries(scope, scope_id);
```

## Migration policy

Migrations are forward-only, numbered, and applied via a single migration tool (chosen in
`06_TECHNOLOGY_STACK.md`). No migration may be edited after it has run in any environment;
a mistake is corrected by a new migration, never by rewriting history -- this preserves the
same tamper-evidence principle applied to `audit_events` for the schema itself.

## Transaction boundaries

Every state-changing API call wraps its `INSERT`/`UPDATE` on a primary table and its
corresponding `audit_events` insert in a single database transaction (REQ-AUD-001) -- if the
audit insert fails, the primary write is rolled back.
