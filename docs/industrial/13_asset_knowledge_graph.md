# Asset-Centric Industrial Knowledge Graph

> Per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §7. Implemented as ordinary
> PostgreSQL relations — see `06_TECHNOLOGY_STACK.md`'s "Explicitly not used in V1" section for
> why no separate graph database was introduced. "Knowledge graph" here describes a set of
> relationships between existing entities, not a new storage technology.

## The entities

Plant, Unit, Equipment, MaintenanceEvent, Inspection, Incident — defined in
`domain/20_asset_model.md`. Document, DocumentChunk, Evidence — defined in
`domain/06_document_model.md`, `07_knowledge_model.md`, `13_evidence_model.md`.

## The relationships

| Relationship | Cardinality | Implementation |
|---|---|---|
| `located_in` (Unit → Plant, Equipment → Unit) | many-to-one | direct FK, `domain/20_asset_model.md` |
| `maintenance_event`, `inspection`, `incident` (Equipment → event rows) | one-to-many | direct FK, `domain/20_asset_model.md` |
| `extracted_from` (MaintenanceEvent/Inspection/Incident → Document) | many-to-one | `source_document_id` FK, `domain/20_asset_model.md` |
| `governed_by` (Equipment ↔ Document) | many-to-many | join table `equipment_governing_documents(equipment_id, document_id, relationship_note)` — a pump can be governed by multiple SOPs (operating procedure, lockout-tagout procedure), and one SOP can govern multiple pumps of the same model |
| `supersedes` (Document → Document) | one-to-one, optional | `Document.superseded_by` FK, `domain/06_document_model.md` |

## Entity resolution (matching a document mention to an Equipment row)

When an inspection report or maintenance record is ingested, extraction attempts to match any
equipment tag it finds (e.g. "P-204") against existing `Equipment.tag_number` values scoped to
the ingesting workspace's Plant/Unit set:

1. **Exact tag match within the same Unit** — highest confidence, auto-linked.
2. **Exact tag match in a different Unit of the same Plant** — flagged for human confirmation
   rather than auto-linked, since tag numbers are sometimes reused across units.
3. **No match** — the document is still ingested and retrievable normally (existing document
   Q&A is unaffected), but the extracted event has no `equipment_id` link until a human either
   creates the matching Equipment row or manually links it via `ui/23_asset_view.md`.

This reuses the same matching-heuristic pattern already proven in
`industrial/05_document_comparison.md` for document-to-document matching, applied here to
document-to-equipment matching instead.

## Provenance

Every edge in this graph is traceable back to the Document that produced it: an
`extracted_from` edge always carries `source_document_id`; a `governed_by` edge is either
set explicitly by a human (auditable, per `05_ARCHITECTURAL_PRINCIPLES.md` principle 9) or
proposed by extraction and confirmed by a human before being treated as authoritative — the
graph never asserts a relationship the underlying documents don't support, per principle 2
(evidence before assertion).

## Temporal validity

An edge inherits the temporal validity of the Document it came from
(`Document.effective_from`/`effective_until`, `domain/06_document_model.md`) — a
`governed_by` edge to a superseded SOP is not deleted when the SOP is superseded, it's marked
via the SOP's own `effective_until`, so historical queries ("which SOP governed this pump in
2023?") remain answerable rather than silently losing history.

## What this enables

- **Asset history** (`ui/23_asset_view.md`, Demo 4): given an Equipment row, list every
  Inspection/MaintenanceEvent/Incident and every governing Document, ordered by date.
- **Impact analysis** (extends `industrial/06_change_detection.md`'s revision comparison):
  given a changed SOP, find every Equipment row `governed_by` it, to answer "which pumps does
  this procedure change affect?" — the `governed_by` join table is what makes this a database
  query instead of a manual search.
- **Conflict detection input** (`industrial/14_knowledge_conflict_detection.md`): two
  Documents both `governed_by`-linked to the same Equipment, both with `authority = primary`
  and overlapping `effective_from`/`effective_until` ranges, is exactly the structural
  signature of a knowledge conflict worth surfacing.

## What this does not do (V1 scope)

No automatic relationship inference beyond the tag-matching described above — no NLP-based
entity extraction of equipment relationships from free text beyond the tag-number match, and
no automatic `governed_by` linking without either an exact-match auto-link (case 1 above) or
human confirmation (case 2). This keeps the graph's contents exactly as trustworthy as the
documents and human confirmations behind them — consistent with never silently asserting a
relationship the evidence doesn't support.
