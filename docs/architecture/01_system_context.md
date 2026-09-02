# System Context

> Directory: `docs/architecture/` · File: `01_system_context.md` · Kind: **structural view**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: _(first document in this directory)_ · Next: `02_logical_architecture.md`

## Purpose

**System Context** documents a cross-cutting view of how components, trust zones, and deployment topologies relate for "system context" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** System Context is a named structural view within the `architecture/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for System Context at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to System Context require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. System Context is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of System Context enforces the same rule set described here — a feature that reads
   System Context differently than documented here is a bug in that feature, not a variant.
3. Where System Context interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where System Context interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/05_ARCHITECTURAL_PRINCIPLES.md`

## Acceptance criteria

- [ ] System Context behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of System Context contradicts a related document listed above.
- [ ] System Context is covered by at least one test referenced from `docs/testing/`.
- [ ] System Context requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to System Context, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of System Context that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about System Context are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
