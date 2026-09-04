# Evidence, Citation

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Evidence.id primary key |
| `task_id` | uuid FK → Task.id | yes | — | which task's answer this evidence supports |
| `source_document_id` | uuid FK → Document.id | yes | — | — |
| `document_version` | integer | yes | — | Document.version at retrieval time, for point-in-time correctness |
| `chunk_id` | uuid FK → DocumentChunk.id | yes | — | — |
| `page_number` | integer | no | null | copied from chunk at creation time |
| `source_hash` | char(64) | yes | — | Document.sha256 at retrieval time |
| `retrieval_method` | enum(vector,keyword,hybrid) | yes | — | REQ-FUNC-005 |
| `confidence` | real | no | null | retrieval/rerank score, 0.0–1.0 |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

**Citation** (not a separate table): the rendered form of an Evidence record attached to a specific span of agent output text — stored as `{evidence_id, text_span_start, text_span_end}` inline in the Message's `content` jsonb. An agent MUST NOT emit a claim without a matching Evidence row (REQ-FUNC-005) — this is enforced in `features/14_evidence_and_provenance/09_unsupported_claim_detection.md`, not merely a convention.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
