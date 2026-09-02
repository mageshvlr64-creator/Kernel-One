# Resource Testing

> Directory: `docs/testing/` · File: `26_resource_testing.md` · Kind: **test approach**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `25_load_testing.md` · Next: `27_recovery_testing.md`

## Purpose

**Resource Testing** documents what must be covered and how pass/fail is judged for "resource testing" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Resource Testing is a named test approach within the `testing/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Resource Testing at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Resource Testing require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Resource Testing is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Resource Testing enforces the same rule set described here — a feature that reads
   Resource Testing differently than documented here is a bug in that feature, not a variant.
3. Where Resource Testing interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Resource Testing interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/testing/01_testing_strategy.md`
- `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`

## Acceptance criteria

- [ ] Resource Testing behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Resource Testing contradicts a related document listed above.
- [ ] Resource Testing is covered by at least one test referenced from `docs/testing/`.
- [ ] Resource Testing requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Resource Testing, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Resource Testing that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Resource Testing are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
