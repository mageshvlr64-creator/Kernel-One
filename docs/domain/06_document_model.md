# Document

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `workspace_id` | uuid FK → Workspace.id | yes | — | on delete cascade to soft-delete |
| `filename` | text | yes | — | original upload filename, sanitized |
| `mime_type` | text | yes | — | detected server-side, not trusted from client header |
| `size_bytes` | bigint | yes | — | ≤ 200MB (CONFIG DEFAULT, `16_ENVIRONMENT_AND_CONFIGURATION.md`) |
| `sha256` | char(64) | yes | — | content hash, used for dedup and provenance |
| `storage_uri` | text | yes | — | MinIO object path; never exposed directly to clients |
| `classification` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | INTERNAL | set at upload, may be elevated later, never silently lowered |
| `state` | enum per docs/runtime/_state_machines_canonical.md#document | yes | UPLOADED | see canonical Document state machine |
| `version` | integer | yes | 1 | incremented on re-upload of same logical document |
| `uploaded_by` | uuid FK → User.id | yes | — | on delete restrict |
| `created_at` | timestamptz | yes | now() | immutable |
| `deleted_at` | timestamptz | no | null | soft-delete |

## Notes

Lifecycle: see `docs/runtime/_state_machines_canonical.md#document`. A Document owns zero or more DocumentChunk rows (created during INDEXING) and is the classification anchor that propagates to derived Evidence/Artifact rows (REQ-DATA-001).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
