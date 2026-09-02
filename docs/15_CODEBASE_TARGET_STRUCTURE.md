# Codebase Target Structure

> Root specification document · `docs/15_CODEBASE_TARGET_STRUCTURE.md`
> Previous: `14_AI_IMPLEMENTATION_PROTOCOL.md` · Next: `16_ENVIRONMENT_AND_CONFIGURATION.md`

## Purpose

This document defines the target repository layout the code (not the docs) should converge on for the Sovereign AI Workbench (SIH26176).

## Why this document exists

Every other document in this tree — every file under `features/`, `architecture/`,
`api/`, and so on — assumes the reader already agrees with what's written here. Rather than
repeat these ground rules in 650 places, they live once, in this file.

## Content

1. **Statement.** Codebase Target Structure is authoritative for its topic across the entire Sovereign AI Workbench
   specification; no feature-level document may contradict it without first updating it here.
2. **Cross-cutting application.** Every feature group under `docs/features/` is expected to be
   consistent with Codebase Target Structure — if a reviewer finds a feature file that conflicts with this
   document, the feature file is wrong, not this one, unless this document is explicitly
   revised (with a note in `20_DECISION_LOG.md`).
3. **Enforcement.** Adherence to Codebase Target Structure is part of `11_DEFINITION_OF_DONE.md` and
   `12_GLOBAL_ACCEPTANCE_CRITERIA.md` — it is checked, not assumed.

## Related documents

- `docs/13_DEVELOPER_RULES.md`
- `docs/14_AI_IMPLEMENTATION_PROTOCOL.md`
- `docs/18_DOCUMENTATION_INDEX.md`

## Maintenance

Changes to Codebase Target Structure must be reflected in `docs/20_DECISION_LOG.md` with the date, the reason
for the change, and which downstream documents were checked for consistency afterward.
