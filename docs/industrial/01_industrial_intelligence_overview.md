# Industrial Intelligence Overview

> Directory: `docs/industrial/` · File: `01_industrial_intelligence_overview.md` · Kind: **industrial capability**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: _(first document in this directory)_ · Next: `02_inspection_reports.md`

## Purpose

**Industrial Intelligence Overview** documents a domain-specific capability built on the core platform for "industrial intelligence overview" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Industrial Intelligence Overview is a named industrial capability within the `industrial/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Industrial Intelligence Overview at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Industrial Intelligence Overview require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Industrial Intelligence Overview is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Industrial Intelligence Overview enforces the same rule set described here — a feature that reads
   Industrial Intelligence Overview differently than documented here is a bug in that feature, not a variant.
3. Where Industrial Intelligence Overview interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Industrial Intelligence Overview interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/industrial/01_industrial_intelligence_overview.md`
- `docs/features/14_evidence_and_provenance.md`

## Acceptance criteria

- [ ] Industrial Intelligence Overview behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Industrial Intelligence Overview contradicts a related document listed above.
- [ ] Industrial Intelligence Overview is covered by at least one test referenced from `docs/testing/`.
- [ ] Industrial Intelligence Overview requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Industrial Intelligence Overview, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Industrial Intelligence Overview that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Industrial Intelligence Overview are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
