# Plant, Unit, Equipment, MaintenanceEvent, Inspection, Incident

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.
>
> Added per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §6 — this is what makes the
> platform asset-centric rather than document-type-centric: an Equipment row is something you
> can navigate to, ask "what's its history," and reason about independently of any single
> document that happens to mention it.

## Why this file exists

Before this file, `industrial/` workflows operated on Document *types* (inspection reports,
maintenance records, SOPs) with no entity underneath them representing the physical thing
those documents are about. Two inspection reports for the same pump had no structural
relationship to each other except both mentioning a similar-looking equipment tag in free
text. These six entities give the industrial layer something real to point at: a specific
pump, a specific unit, with real foreign keys, not text matching.

Per the master prompt's own MVP guidance for §7, this stays in PostgreSQL as ordinary
relational tables — no separate graph database is introduced (see `06_TECHNOLOGY_STACK.md`,
"Explicitly not used in V1").

## Fields — Plant

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `organization_id` | uuid FK → Organization.id | yes | — | on delete cascade to soft-delete |
| `name` | text | yes | — | e.g. "Vadodara Refinery" |
| `location` | text | no | null | free text; not geocoded in V1 |
| `created_at` | timestamptz | yes | now() | immutable |
| `deleted_at` | timestamptz | no | null | soft-delete |

## Fields — Unit

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `plant_id` | uuid FK → Plant.id | yes | — | on delete cascade to soft-delete |
| `name` | text | yes | — | e.g. "Crude Distillation Unit 2" |
| `unit_type` | text | no | null | free text classification, e.g. "distillation," "utilities" |
| `created_at` | timestamptz | yes | now() | immutable |
| `deleted_at` | timestamptz | no | null | soft-delete |

## Fields — Equipment

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `unit_id` | uuid FK → Unit.id | yes | — | on delete cascade to soft-delete |
| `tag_number` | text | yes | — | unique within `unit_id`; the physical/P&ID tag, e.g. "P-204" |
| `name` | text | yes | — | e.g. "Feed Pump P-204" |
| `equipment_type` | text | no | null | free text, e.g. "centrifugal pump," "pressure vessel" |
| `manufacturer` | text | no | null | — |
| `model_number` | text | no | null | — |
| `status` | enum(operational,degraded,down,decommissioned) | yes | operational | operator-set; not automatically derived from inspection findings in V1 (a human confirms status changes — see `05_ARCHITECTURAL_PRINCIPLES.md` principle 6) |
| `commissioned_at` | date | no | null | — |
| `created_at` | timestamptz | yes | now() | immutable |
| `deleted_at` | timestamptz | no | null | soft-delete |

## Fields — MaintenanceEvent

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `equipment_id` | uuid FK → Equipment.id | yes | — | on delete cascade to soft-delete |
| `source_document_id` | uuid FK → Document.id | no | null | the maintenance record this event was extracted from, if any — links back to `industrial/03_maintenance_records.md`'s extraction output |
| `event_type` | text | no | null | free text, e.g. "seal replacement," "scheduled service" |
| `performed_at` | date | no | null | — |
| `notes` | text | no | null | — |
| `created_at` | timestamptz | yes | now() | immutable |

## Fields — Inspection

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `equipment_id` | uuid FK → Equipment.id | yes | — | on delete cascade to soft-delete |
| `source_document_id` | uuid FK → Document.id | no | null | the inspection report this row was extracted from — links back to `industrial/02_inspection_reports.md` |
| `inspected_at` | date | no | null | — |
| `finding_summary` | text | no | null | — |
| `severity` | enum(informational,minor,major,critical) | no | null | — |
| `created_at` | timestamptz | yes | now() | immutable |

## Fields — Incident

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `equipment_id` | uuid FK → Equipment.id | yes | — | on delete cascade to soft-delete |
| `source_document_id` | uuid FK → Document.id | no | null | — |
| `occurred_at` | date | no | null | — |
| `description` | text | no | null | — |
| `severity` | enum(informational,minor,major,critical) | no | null | — |
| `created_at` | timestamptz | yes | now() | immutable |

## Relationship to Document and Evidence

`MaintenanceEvent.source_document_id`, `Inspection.source_document_id`, and
`Incident.source_document_id` are the concrete link between "a document says X happened to
this pump" and "this pump has a history" — this is the relational implementation of the
asset-centric knowledge graph described in `industrial/13_asset_knowledge_graph.md`. An
Evidence row cited in an answer about a specific piece of Equipment can be traced: Answer →
Evidence → Document → (Inspection|MaintenanceEvent|Incident) → Equipment → Unit → Plant.

Governing-document relationships (which SOPs/manuals apply to a given Equipment) are
many-to-many and are covered separately in `industrial/13_asset_knowledge_graph.md`'s
`governed_by` relationship, not as a column on Equipment, since one document can govern many
equipment items and vice versa.

## Ownership

Plant/Unit/Equipment are created and edited through the industrial intelligence UI
(`ui/23_asset_view.md`) by roles with `Equipment:write` per `reference/05_permission_matrix.md`
— typically an Operator or Administrator, not created implicitly by document ingestion.
MaintenanceEvent/Inspection/Incident rows are created by the industrial extraction workflows
(`industrial/02_inspection_reports.md`, `03_maintenance_records.md`) when a matching Equipment
tag is found in an ingested document, with the row always reviewable and correctable by a
human, per `05_ARCHITECTURAL_PRINCIPLES.md` principle 6 — the extraction proposes, it does not
silently commit an event to an asset's permanent history without that being visible.

## Audit behavior

Every insert/update/soft-delete on any table above produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001, same as every
other entity in this tree.
