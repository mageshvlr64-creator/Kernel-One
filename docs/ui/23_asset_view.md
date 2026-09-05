# Asset View

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows. Per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §43 — the screen that turns
> this system into an industrial intelligence application rather than a document chatbot with
> an industrial vocabulary.

## Purpose

Give a single Equipment row (`domain/20_asset_model.md`) a page: its identity, current status,
and full history, assembled from every Document/Inspection/MaintenanceEvent/Incident linked to
it via `industrial/13_asset_knowledge_graph.md`.

## Route

`/assets` — list/search view (all Equipment visible to the user's workspace/classification
scope). `/assets/:equipmentId` — detail view, this screen's primary spec below.

## User roles

All roles with `Equipment:read` (`reference/05_permission_matrix.md`) may view. Editing
status or governing-document links requires `Equipment:write`.

## Key elements — list view (`/assets`)

- Search/filter by tag number, name, Plant, Unit, status.
- Table: Tag number, Name, Unit, Status (colored per `status` enum), last inspection date.

## Key elements — detail view (`/assets/:equipmentId`)

- **Header:** tag number, name, status badge, Plant / Unit breadcrumb.
- **Identity panel:** manufacturer, model number, commissioned date.
- **Maintenance history:** chronological list of `MaintenanceEvent` rows, each linking to its
  `source_document_id` (opens `ui/15_knowledge_browser.md`'s document view at the relevant
  page/section, using `Evidence.section_reference` where available,
  `domain/13_evidence_model.md`).
- **Inspection history:** chronological list of `Inspection` rows, same source-document linking
  as above, with severity badges.
- **Incidents:** chronological list of `Incident` rows, same pattern, with severity badges.
- **Related SOPs and revisions:** every Document linked via the `governed_by` edge
  (`industrial/13_asset_knowledge_graph.md`), showing `Document.authority` and current
  `effective_from`/`effective_until` — a superseded SOP is shown greyed out with a "superseded
  by" link, not hidden, so history remains visible.
- **Known conflicts:** any unresolved `CONFLICT DETECTED` records
  (`industrial/14_knowledge_conflict_detection.md`) touching this Equipment's governing
  documents, surfaced prominently rather than buried in the SOP list.
- **Risks / AI insights:** a free-text agent-generated summary (itself Evidence-backed per
  `05_ARCHITECTURAL_PRINCIPLES.md` principle 2 — every sentence here links back to the specific
  Inspection/Incident/MaintenanceEvent row that supports it, same citation mechanism as
  `ui/09_evidence_panel.md`) — e.g. "3 inspections in the last year noted seal wear; last
  maintenance record shows the seal was not replaced." This panel never states something the
  history above doesn't already show — it summarizes, it doesn't add unverifiable claims.

## Actions available

- Update `status` (gated by `Equipment:write`).
- Add/remove a `governed_by` link to a Document (gated by `Equipment:write`), with the same
  human-confirmation flow described in `industrial/13_asset_knowledge_graph.md`'s entity
  resolution section for case 2 (ambiguous tag matches).
- Resolve a conflict shown in the Known conflicts panel (gated by `Document:reclassify`,
  navigates to the resolution flow in `industrial/14_knowledge_conflict_detection.md`).
- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: "No equipment recorded yet — add one to start tracking maintenance and inspection
history" (list view only; an unlinked-but-ingested document still exists independently, see
`industrial/13_asset_knowledge_graph.md`'s "no match" case). Loading: standard skeleton per
`ui/02_design_system.md`. Error: standard error banner. Permission-denied: `Equipment:read`
required for `/assets/:equipmentId`, `20_permission_denied_states.md`'s 403 page otherwise.

## Related

- `domain/20_asset_model.md` for the entities this screen renders.
- `industrial/13_asset_knowledge_graph.md` for how the relationships shown here are computed.
- `industrial/14_knowledge_conflict_detection.md` for the Known conflicts panel's data source.
- `reference/05_permission_matrix.md` for exactly which role sees which control.
- The API endpoint(s) this screen calls, under `docs/api/`.
