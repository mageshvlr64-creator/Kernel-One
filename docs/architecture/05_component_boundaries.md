# Component Boundaries

> Directory: `docs/architecture/` · File: `05_component_boundaries.md` · Kind: **structural view**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `04_deployment_architecture.md` · Next: `06_service_boundaries.md`

## Purpose

**Component Boundaries** documents a cross-cutting view of how components, trust zones, and deployment topologies relate for "component boundaries" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Component Boundaries is a named structural view within the `architecture/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Component Boundaries at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Component Boundaries require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Component Boundaries is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Component Boundaries enforces the same rule set described here — a feature that reads
   Component Boundaries differently than documented here is a bug in that feature, not a variant.
3. Where Component Boundaries interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Component Boundaries interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/05_ARCHITECTURAL_PRINCIPLES.md`

## Acceptance criteria

- [ ] Component Boundaries behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Component Boundaries contradicts a related document listed above.
- [ ] Component Boundaries is covered by at least one test referenced from `docs/testing/`.
- [ ] Component Boundaries requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Component Boundaries, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Component Boundaries that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Component Boundaries are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
