# Industrial Workflow Boundaries

> Directory: `docs/industrial/` · File: `12_industrial_workflow_boundaries.md` · Kind: **industrial capability**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `11_calculation_verification.md` · Next: _(last document in this directory)_

## Purpose

**Industrial Workflow Boundaries** documents a domain-specific capability built on the core platform for "industrial workflow boundaries" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Industrial Workflow Boundaries is a named industrial capability within the `industrial/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Industrial Workflow Boundaries at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Industrial Workflow Boundaries require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Industrial Workflow Boundaries is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Industrial Workflow Boundaries enforces the same rule set described here — a feature that reads
   Industrial Workflow Boundaries differently than documented here is a bug in that feature, not a variant.
3. Where Industrial Workflow Boundaries interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Industrial Workflow Boundaries interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/industrial/01_industrial_intelligence_overview.md`
- `docs/features/14_evidence_and_provenance.md`

## Acceptance criteria

- [ ] Industrial Workflow Boundaries behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Industrial Workflow Boundaries contradicts a related document listed above.
- [ ] Industrial Workflow Boundaries is covered by at least one test referenced from `docs/testing/`.
- [ ] Industrial Workflow Boundaries requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Industrial Workflow Boundaries, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Industrial Workflow Boundaries that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Industrial Workflow Boundaries are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
