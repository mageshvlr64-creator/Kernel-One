# Demo Data

> Directory: `docs/demo/` · File: `03_demo_data.md` · Kind: **demo beat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `02_demo_environment.md` · Next: `04_demo_setup.md`

## Purpose

**Demo Data** documents one scripted moment in the jury walkthrough for "demo data" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Demo Data is a named demo beat within the `demo/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Demo Data at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Demo Data require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Demo Data is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Demo Data enforces the same rule set described here — a feature that reads
   Demo Data differently than documented here is a bug in that feature, not a variant.
3. Where Demo Data interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Demo Data interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Demo Data behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Demo Data contradicts a related document listed above.
- [ ] Demo Data is covered by at least one test referenced from `docs/testing/`.
- [ ] Demo Data requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Demo Data, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Demo Data that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Demo Data are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
