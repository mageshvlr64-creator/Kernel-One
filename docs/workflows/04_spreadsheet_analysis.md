# Spreadsheet Analysis

> Directory: `docs/workflows/` · File: `04_spreadsheet_analysis.md` · Kind: **end-to-end workflow**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `03_multimodal_drawing.md` · Next: `05_document_qa.md`

## Purpose

**Spreadsheet Analysis** documents a full user scenario crossing multiple features for "spreadsheet analysis" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Spreadsheet Analysis is a named end-to-end workflow within the `workflows/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Spreadsheet Analysis at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Spreadsheet Analysis require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Spreadsheet Analysis is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Spreadsheet Analysis enforces the same rule set described here — a feature that reads
   Spreadsheet Analysis differently than documented here is a bug in that feature, not a variant.
3. Where Spreadsheet Analysis interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Spreadsheet Analysis interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Spreadsheet Analysis behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Spreadsheet Analysis contradicts a related document listed above.
- [ ] Spreadsheet Analysis is covered by at least one test referenced from `docs/testing/`.
- [ ] Spreadsheet Analysis requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Spreadsheet Analysis, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Spreadsheet Analysis that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Spreadsheet Analysis are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
