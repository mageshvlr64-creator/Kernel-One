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
| `authority` | enum(primary,secondary,reference) | yes | secondary | `primary` = the governing document for its subject (e.g. the current SOP for a procedure); `secondary` = a related but non-governing document (e.g. a maintenance manual note on the same procedure); `reference` = background material with no authority claim. Set at upload by the uploader, changeable only by a role with `Document:reclassify` per `reference/05_permission_matrix.md`. Used by `industrial/14_knowledge_conflict_detection.md` to resolve conflicts between two Documents that both claim to be current |
| `effective_from` | timestamptz | no | `created_at` | when this Document version became the applicable one for its subject; enables "what was applicable on date X" queries (`SIH26117_Documentation_Refactor_Master_Prompt.txt` §38) |
| `effective_until` | timestamptz | no | null | when this Document version stopped being applicable; null means "still current." Set automatically when `superseded_by` is set on this row |
| `superseded_by` | uuid FK → Document.id | no | null | points to the Document row that replaced this one, when applicable; distinct from `version` (which tracks re-uploads of the *same* logical document) — `superseded_by` links two *different* Document rows where one supersedes the other, e.g. a new SOP number replacing an old one |
| `uploaded_by` | uuid FK → User.id | yes | — | on delete restrict |
| `created_at` | timestamptz | yes | now() | immutable |
| `deleted_at` | timestamptz | no | null | soft-delete |

## Notes

Lifecycle: see `docs/runtime/_state_machines_canonical.md#document`. A Document owns zero or more DocumentChunk rows (created during INDEXING) and is the classification anchor that propagates to derived Evidence/Artifact rows (REQ-DATA-001).

## Temporal validity and knowledge trust

`authority`, `effective_from`, `effective_until`, and `superseded_by` together implement the
knowledge-trust-model properties required by the master prompt (§37, §38): a query scoped to
a past date filters retrieval to Documents where `effective_from <= query_date <
COALESCE(effective_until, 'infinity')`, so a question like "what was the applicable procedure
in 2024?" returns the version that was actually in force then, not just the newest upload.
This filter is applied in `features/13_knowledge_fabric/09_hybrid_search.md`'s retrieval
query — **status: schema fields defined here; the retrieval-time filter itself is a
`features/13_knowledge_fabric/` implementation item, tracked as a V1 item not yet wired into
the default (undated) query path.** An undated query ignores these fields and returns the
current (`effective_until IS NULL`) version, which is today's default behavior and remains
correct for the common case.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
