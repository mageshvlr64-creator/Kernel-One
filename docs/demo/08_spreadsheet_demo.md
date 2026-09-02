# Spreadsheet Demo

> Directory: `docs/demo/` · File: `08_spreadsheet_demo.md` · Kind: **demo beat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `07_multimodal_demo.md` · Next: `09_execution_graph_demo.md`

## Purpose

**Spreadsheet Demo** documents one scripted moment in the jury walkthrough for "spreadsheet demo" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Spreadsheet Demo is a named demo beat within the `demo/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Spreadsheet Demo at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Spreadsheet Demo require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Spreadsheet Demo is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Spreadsheet Demo enforces the same rule set described here — a feature that reads
   Spreadsheet Demo differently than documented here is a bug in that feature, not a variant.
3. Where Spreadsheet Demo interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Spreadsheet Demo interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Spreadsheet Demo behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Spreadsheet Demo contradicts a related document listed above.
- [ ] Spreadsheet Demo is covered by at least one test referenced from `docs/testing/`.
- [ ] Spreadsheet Demo requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Spreadsheet Demo, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Spreadsheet Demo that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Spreadsheet Demo are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
