# Integration Testing

> Directory: `docs/testing/` · File: `03_integration_testing.md` · Kind: **test approach**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `02_unit_testing.md` · Next: `04_contract_testing.md`

## Purpose

**Integration Testing** documents what must be covered and how pass/fail is judged for "integration testing" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Integration Testing is a named test approach within the `testing/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Integration Testing at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Integration Testing require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Integration Testing is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Integration Testing enforces the same rule set described here — a feature that reads
   Integration Testing differently than documented here is a bug in that feature, not a variant.
3. Where Integration Testing interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Integration Testing interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/testing/01_testing_strategy.md`
- `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`

## Acceptance criteria

- [ ] Integration Testing behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Integration Testing contradicts a related document listed above.
- [ ] Integration Testing is covered by at least one test referenced from `docs/testing/`.
- [ ] Integration Testing requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Integration Testing, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Integration Testing that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Integration Testing are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
