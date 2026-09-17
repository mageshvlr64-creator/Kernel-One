# Documentation Index

> Root specification document · `docs/18_DOCUMENTATION_INDEX.md`
> Previous: `17_SOURCE_TRACEABILITY.md` · Next: `19_GLOSSARY.md`

## Purpose

This document defines a flat index of every document in this tree, for fast lookup for the Sovereign AI Workbench (SIH26117).

## Why this document exists

Every other document in this tree — every file under `features/`, `architecture/`,
`api/`, and so on — assumes the reader already agrees with what's written here. Rather than
repeat these ground rules in 650 places, they live once, in this file.

## Content

1. **Statement.** Documentation Index is authoritative for its topic across the entire Sovereign AI Workbench
   specification; no feature-level document may contradict it without first updating it here.
2. **Cross-cutting application.** Every feature group under `docs/features/` is expected to be
   consistent with Documentation Index — if a reviewer finds a feature file that conflicts with this
   document, the feature file is wrong, not this one, unless this document is explicitly
   revised (with a note in `20_DECISION_LOG.md`).
3. **Enforcement.** Adherence to Documentation Index is part of `11_DEFINITION_OF_DONE.md` and
   `12_GLOBAL_ACCEPTANCE_CRITERIA.md` — it is checked, not assumed.

## New root files added during the audit pass

This specification also includes `21_COMPETITIVE_POSITIONING.md` (prior-art comparison,
Upgrade Prompt §52), `runtime/_state_machines_canonical.md` (the single source for all
entity state machines, referenced by `runtime/04..09_*_state_machine.md` pointer files),
`22_REFACTOR_AUDIT_REPORT.md` (the 2026-09-04 identifier-correction and consistency audit —
see `20_DECISION_LOG.md` DEC-018/DEC-019), `MASTER_PROMPT_COMPLIANCE_AUDIT.md` and
`DETAILED_FINDINGS_AND_REMEDIATION_PLAN.md` (the 63-section compliance audit and per-item
remediation plan that DEC-020/DEC-021 implement), and `23_SERVICE_MAP_AS_BUILT.md` (the
as-built service map and pipeline flow — what is actually implemented versus the build
order; created 2026-09-16, see `20_DECISION_LOG.md` DEC-026).

## New non-root files added during the compliance remediation pass (DEC-020)

- `domain/20_asset_model.md` — Plant/Unit/Equipment/MaintenanceEvent/Inspection/Incident entities.
- `industrial/13_asset_knowledge_graph.md` — asset-centric relationship model.
- `industrial/14_knowledge_conflict_detection.md` — cross-document contradiction detection.
- `ui/23_asset_view.md` — the equipment/asset screen.

## Repo-root files (not under `docs/`, but essential reading — see DEC-022)

- `../TEAM.md` — the six-character build-ownership split, read by any agent before writing code.
- `../CHANGELOG.md` — the running build log every character appends to.

## Related documents

- `docs/13_DEVELOPER_RULES.md`
- `docs/14_AI_IMPLEMENTATION_PROTOCOL.md`
- `docs/18_DOCUMENTATION_INDEX.md`

## Maintenance

Changes to Documentation Index must be reflected in `docs/20_DECISION_LOG.md` with the date, the reason
for the change, and which downstream documents were checked for consistency afterward.
