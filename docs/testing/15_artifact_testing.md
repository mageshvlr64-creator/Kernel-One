# Artifact Testing

> Covers `features/15_artifact_engine/` — generation correctness and provenance.

## Required tests

- Each supported type (DOCX/PPTX/XLSX/PDF/CSV/JSON/Markdown) generates a file that
  successfully re-opens/parses (the same validation check the state machine's `VALIDATING`
  stage performs, `runtime/_state_machines_canonical.md#artifact`).
- `evidence_ids` on the generated Artifact correctly reference the Evidence used to produce it
  (`features/15_artifact_engine/10_source_provenance.md`).
- Classification computation: an artifact citing CONFIDENTIAL and INTERNAL evidence is itself
  tagged CONFIDENTIAL (`TEST-CLASS-001`, shared with `19_rbac_testing.md`/classification
  testing).
