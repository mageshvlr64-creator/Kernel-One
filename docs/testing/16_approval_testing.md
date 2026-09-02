# Approval Testing

> Directory: `docs/testing/` · File: `16_approval_testing.md` · Kind: **test approach**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `15_artifact_testing.md` · Next: `17_audit_testing.md`

## Purpose

**Approval Testing** documents what must be covered and how pass/fail is judged for "approval testing" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Approval Testing is a named test approach within the `testing/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Approval Testing at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Approval Testing require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Approval Testing is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Approval Testing enforces the same rule set described here — a feature that reads
   Approval Testing differently than documented here is a bug in that feature, not a variant.
3. Where Approval Testing interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Approval Testing interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/testing/01_testing_strategy.md`
- `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`

## Acceptance criteria

- [ ] Approval Testing behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Approval Testing contradicts a related document listed above.
- [ ] Approval Testing is covered by at least one test referenced from `docs/testing/`.
- [ ] Approval Testing requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Approval Testing, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Approval Testing that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Approval Testing are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
