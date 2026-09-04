# Documentation Index

> Root specification document · `docs/18_DOCUMENTATION_INDEX.md`
> Previous: `17_SOURCE_TRACEABILITY.md` · Next: `19_GLOSSARY.md`

## Purpose

This document defines a flat index of every document in this tree, for fast lookup for the Sovereign AI Workbench (SIH26176).

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
Upgrade Prompt §52) and `runtime/_state_machines_canonical.md` (the single source for all
entity state machines, referenced by `runtime/04..09_*_state_machine.md` pointer files).

## Related documents

- `docs/13_DEVELOPER_RULES.md`
- `docs/14_AI_IMPLEMENTATION_PROTOCOL.md`
- `docs/18_DOCUMENTATION_INDEX.md`

## Maintenance

Changes to Documentation Index must be reflected in `docs/20_DECISION_LOG.md` with the date, the reason
for the change, and which downstream documents were checked for consistency afterward.
