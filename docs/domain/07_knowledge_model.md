# DocumentChunk

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `document_id` | uuid FK → Document.id | yes | — | on delete cascade |
| `chunk_index` | integer | yes | — | 0-based order within document |
| `page_number` | integer | no | null | null for non-paginated formats (e.g. CSV) |
| `bbox` | jsonb | no | null | bounding box `[x0,y0,x1,y1]` for native PDFs; null if unavailable (e.g. OCR without layout) |
| `text` | text | yes | — | chunk content, 200–800 tokens (CONFIG DEFAULT chunking window, `features/13_knowledge_fabric/04_chunking.md`) |
| `embedding` | vector(768) | yes | — | pgvector column; dimension fixed by the configured embedding model |
| `ocr_confidence` | real | no | null | 0.0–1.0; null if not OCR-derived |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

Created during Document INDEXING. Indexed by both an HNSW vector index (pgvector) and a PostgreSQL `tsvector` GIN index for hybrid search (`features/13_knowledge_fabric/09_hybrid_search.md`). Inherits its parent Document's classification for retrieval filtering (REQ-FUNC-004) — never queried without that filter applied.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
