# Rag Testing

> Directory: `docs/testing/` · File: `09_rag_testing.md` · Kind: **test approach**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `08_model_router_testing.md` · Next: `10_document_pipeline_testing.md`

## Purpose

**Rag Testing** documents what must be covered and how pass/fail is judged for "rag testing" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Rag Testing is a named test approach within the `testing/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Rag Testing at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Rag Testing require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Rag Testing is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Rag Testing enforces the same rule set described here — a feature that reads
   Rag Testing differently than documented here is a bug in that feature, not a variant.
3. Where Rag Testing interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Rag Testing interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/testing/01_testing_strategy.md`
- `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`

## Acceptance criteria

- [ ] Rag Testing behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Rag Testing contradicts a related document listed above.
- [ ] Rag Testing is covered by at least one test referenced from `docs/testing/`.
- [ ] Rag Testing requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Rag Testing, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Rag Testing that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Rag Testing are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
