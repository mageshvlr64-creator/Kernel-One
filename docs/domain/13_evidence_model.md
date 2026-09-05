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
| `section_reference` | text | no | null | copied from chunk at creation time — the document's own section/clause label (e.g. "§4.2", "Table 3"), when the source format exposes one; completes the Source→Version→Page/Section→Chunk chain from `SIH26117_Documentation_Refactor_Master_Prompt.txt` §10 |
| `source_hash` | char(64) | yes | — | Document.sha256 at retrieval time |
| `retrieval_method` | enum(vector,keyword,hybrid) | yes | — | REQ-FUNC-005 |
| `source_authority` | enum, matches `Document.authority` | yes | — | denormalized from `Document.authority` at retrieval time, same point-in-time-correctness reasoning as `document_version` — see Document fields below |
| `verification_status` | enum(unverified,supported,contradicted,unsupported) | yes | `unverified` | set by the verification pipeline (`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`) after retrieval, before the citation is shown to the user; `contradicted` means another Evidence row for the same claim disagrees — see `industrial/14_knowledge_conflict_detection.md` |
| `confidence` | real | no | null | retrieval/rerank ranking score, 0.0–1.0 — an internal ranking signal only, **not** displayed to the user as a bare probability; see Confidence methodology note below |
| `created_at` | timestamptz | yes | now() | immutable |

## Confidence methodology (per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §12)

`confidence` is the retriever/reranker's own similarity or relevance score. It is useful for
*ranking* which evidence to surface first, and is retained for that purpose. It is **not**
calibrated against ground-truth correctness, and must never be presented to a user as
"this answer is 94% likely to be correct" — no calibration study backs that interpretation,
and presenting it that way is explicitly the failure mode the master prompt's §12 warns
against.

What *is* shown to the user (`ui/09_evidence_panel.md`) is the qualitative representation
built from the fields above, not the raw number:

- **Evidence coverage** — how many of the answer's claims have a matching Evidence row at all.
- **Source authority** — from `source_authority` above (was this a primary/authoritative
  document, or a secondary reference?).
- **Freshness** — derived from `Document.effective_from`/`effective_until` (see the Document
  fields in `06_document_model.md`) — is this the currently-applicable revision?
- **Cross-source agreement / contradictions** — from `verification_status` above — did another
  source disagree?

The raw `confidence` score may still be exposed in a detail/debug view for operators who want
it, clearly labeled as a retrieval-ranking signal, never as a correctness probability.

## Notes

**Citation** (not a separate table): the rendered form of an Evidence record attached to a specific span of agent output text — stored as `{evidence_id, text_span_start, text_span_end}` inline in the Message's `content` jsonb. An agent MUST NOT emit a claim without a matching Evidence row (REQ-FUNC-005) — this is enforced in `features/14_evidence_and_provenance/09_unsupported_claim_detection.md`, not merely a convention.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
