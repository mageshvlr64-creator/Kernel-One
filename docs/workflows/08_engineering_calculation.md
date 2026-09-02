# Engineering Calculation

> Directory: `docs/workflows/` · File: `08_engineering_calculation.md` · Kind: **end-to-end workflow**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `07_report_generation.md` · Next: `09_approval_workflow.md`

## Purpose

**Engineering Calculation** documents a full user scenario crossing multiple features for "engineering calculation" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Engineering Calculation is a named end-to-end workflow within the `workflows/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Engineering Calculation at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Engineering Calculation require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Engineering Calculation is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Engineering Calculation enforces the same rule set described here — a feature that reads
   Engineering Calculation differently than documented here is a bug in that feature, not a variant.
3. Where Engineering Calculation interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Engineering Calculation interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Engineering Calculation behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Engineering Calculation contradicts a related document listed above.
- [ ] Engineering Calculation is covered by at least one test referenced from `docs/testing/`.
- [ ] Engineering Calculation requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Engineering Calculation, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Engineering Calculation that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Engineering Calculation are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
