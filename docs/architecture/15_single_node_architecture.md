# Single Node Architecture

> Directory: `docs/architecture/` · File: `15_single_node_architecture.md` · Kind: **structural view**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `14_scaling_strategy.md` · Next: `16_multi_node_architecture.md`

## Purpose

**Single Node Architecture** documents a cross-cutting view of how components, trust zones, and deployment topologies relate for "single node architecture" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Single Node Architecture is a named structural view within the `architecture/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Single Node Architecture at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Single Node Architecture require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Single Node Architecture is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Single Node Architecture enforces the same rule set described here — a feature that reads
   Single Node Architecture differently than documented here is a bug in that feature, not a variant.
3. Where Single Node Architecture interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Single Node Architecture interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/05_ARCHITECTURAL_PRINCIPLES.md`

## Acceptance criteria

- [ ] Single Node Architecture behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Single Node Architecture contradicts a related document listed above.
- [ ] Single Node Architecture is covered by at least one test referenced from `docs/testing/`.
- [ ] Single Node Architecture requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Single Node Architecture, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Single Node Architecture that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Single Node Architecture are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
