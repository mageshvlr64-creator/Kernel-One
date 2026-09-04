# Artifact

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `task_id` | uuid FK → Task.id | yes | — | source task |
| `type` | enum(docx,pptx,xlsx,pdf,csv,json,markdown,code) | yes | — | — |
| `filename` | text | yes | — | — |
| `storage_uri` | text | yes | — | MinIO object path |
| `checksum` | char(64) | yes | — | sha256 of generated file, computed post-generation |
| `classification` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | computed | max classification of cited Evidence (REQ-DATA-001) |
| `state` | enum per docs/runtime/_state_machines_canonical.md#artifact | yes | CREATED | — |
| `generator_version` | text | yes | — | artifact-engine build/version that produced this file |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

See `docs/runtime/_state_machines_canonical.md#artifact` for lifecycle. An Artifact's `evidence_ids` (array of Evidence.id, jsonb) records provenance for `features/15_artifact_engine/10_source_provenance.md`.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
