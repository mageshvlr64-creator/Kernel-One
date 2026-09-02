# Final Screen

> Directory: `docs/demo/` · File: `14_final_screen.md` · Kind: **demo beat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `13_failure_demo.md` · Next: `15_demo_recovery.md`

## Purpose

**Final Screen** documents one scripted moment in the jury walkthrough for "final screen" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Final Screen is a named demo beat within the `demo/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Final Screen at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Final Screen require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Final Screen is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Final Screen enforces the same rule set described here — a feature that reads
   Final Screen differently than documented here is a bug in that feature, not a variant.
3. Where Final Screen interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Final Screen interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Final Screen behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Final Screen contradicts a related document listed above.
- [ ] Final Screen is covered by at least one test referenced from `docs/testing/`.
- [ ] Final Screen requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Final Screen, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Final Screen that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Final Screen are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
