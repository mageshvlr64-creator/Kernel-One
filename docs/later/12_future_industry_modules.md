# Future Industry Modules (V2+)

> A placeholder for industry-specific modules beyond the industrial/inspection-report focus
> of V1 — e.g. healthcare records, legal document review, financial compliance — each of which
> would need its own domain-specific evidence/classification expectations analogous to
> `industrial/` but is entirely unscoped today.

## Why this exists as a named file rather than being silently absent

Per this specification's own rule (state assumptions explicitly rather than letting them be
implicit), the fact that V1 is industrial/inspection-focused is a deliberate scope choice
(`01_PRODUCT_VISION.md`, `02_SCOPE_AND_NON_GOALS.md`), not an oversight — this file makes clear
that extending to other verticals is anticipated as a V2+ direction, not ruled out
architecturally (the core platform — RAG, evidence, RBAC, classification, audit — is
domain-agnostic; only `industrial/` and `later/01..04` are inspection-domain-specific).

## What would be required to add a new vertical

1. A new top-level directory analogous to `industrial/`, following the same
   committed/aspirational/deferred structure (`industrial/12_industrial_workflow_boundaries.md`
   as the template).
2. A domain-specific evaluation set (`benchmarks/`) before any new-vertical capability is
   presented as more than a caveated description, per the same discipline applied throughout
   `industrial/` and this file's sibling documents.
3. An explicit `DECISION REQUIRED` entry in `20_DECISION_LOG.md` scoping which vertical is
   next and why, rather than accreting verticals ad hoc.
