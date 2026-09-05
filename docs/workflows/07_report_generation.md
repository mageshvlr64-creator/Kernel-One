# Report Generation

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior. Expanded per
> `SIH26117_Documentation_Refactor_Master_Prompt.txt` §44 — a report is a first-class,
> multi-section output, not a wrapper around a chat answer.

## Requirements implemented

features/15_artifact_engine, features/14_evidence_and_provenance, industrial/13_asset_knowledge_graph (partial — see status notes below), industrial/14_knowledge_conflict_detection (partial — see status notes below)

## Report structure

A generated report DOCX contains the following sections, in order. Each section's status below
reflects what can actually be populated today versus what depends on another gap being closed
first — this file does not claim a section is complete when its data source doesn't exist yet.

1. **Executive summary** — 2-4 sentence agent-generated overview of the task's findings.
   *Status: ready.*
2. **Findings** — the substantive answer content, structured by sub-topic if the task covered
   more than one. *Status: ready.*
3. **Evidence** — every citation used, rendered as Source document / version / page / section
   (`domain/13_evidence_model.md`), with the qualitative confidence representation
   (`features/14_evidence_and_provenance/08_confidence.md`) shown per claim, not a bare score.
   *Status: ready.*
4. **Source references** — a deduplicated bibliography of every Document cited, with
   `Document.authority` and current validity window shown. *Status: ready.*
5. **Affected assets** — every Equipment row touched by the task, via
   `industrial/13_asset_knowledge_graph.md`'s `governed_by`/extraction edges.
   *Status: populated only when the task's Evidence rows link to an Equipment — i.e. only for
   tasks that actually touch asset-linked documents. For a task with no asset linkage, this
   section is correctly omitted, not filled with a placeholder.*
6. **Detected conflicts** — any `CONFLICT DETECTED` records
   (`industrial/14_knowledge_conflict_detection.md`) surfaced during the task.
   *Status: populated when conflict detection fires; omitted otherwise, same reasoning as
   Affected assets.*
7. **Changes** — for a document-comparison task, the specific parameter/location changes found
   (`industrial/06_change_detection.md`). *Status: ready for comparison-type tasks; omitted for
   other task types.*
8. **Calculations** — for an engineering-calculation task, the deterministic component's
   inputs, formula, and result (`features/07_calculator_tool/05_deterministic_verification.md`).
   *Status: ready for calculation-type tasks; omitted for other task types.*
9. **Recommendations** — agent-generated, each one citing the Evidence/Finding it's derived
   from — no recommendation appears without a traceable basis, per
   `05_ARCHITECTURAL_PRINCIPLES.md` principle 2. *Status: ready.*
10. **Uncertainty / limitations** — an explicit statement of what the report could *not*
    determine (e.g. "no governing SOP found for Equipment X" or "conflict unresolved, see
    Detected conflicts"), rather than a report that reads as more complete than its underlying
    evidence supports. *Status: ready.*
11. **Approval state** — classification (computed as max of cited Evidence classifications per
    REQ-DATA-001), and whether the report itself required and received approval before export.
    *Status: ready.*

## Steps

1. Agent's findings/answers are compiled into the 11-section structure above, populating only
   the sections applicable to the task type.
2. Artifact classification computed as max(cited Evidence classifications) per REQ-DATA-001.
3. If classification >= CONFIDENTIAL, export requires Approval (`features/16_human_approval/`),
   following the concrete check sequence in `features/20_data_classification/11_export_restrictions.md`.

## Notes

Sections 5 and 6 (Affected assets, Detected conflicts) are the two sections whose data sources
were themselves gaps at the time of the `SIH26117_Documentation_Refactor_Master_Prompt.txt`
compliance audit — `domain/20_asset_model.md`, `industrial/13_asset_knowledge_graph.md`, and
`industrial/14_knowledge_conflict_detection.md` now exist as specifications, so these sections
are specified above rather than deferred, but they remain the two sections most likely to be
empty in an early implementation until those features are actually built and populated with
real data.
