# Shutdown

> Directory: `docs/operations/` · File: `03_shutdown.md` · Kind: **operator procedure**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `02_startup.md` · Next: `04_health_monitoring.md`

## Purpose

**Shutdown** documents a day-to-day runbook step for a human operator for "shutdown" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Shutdown is a named operator procedure within the `operations/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Shutdown at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Shutdown require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Shutdown is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Shutdown enforces the same rule set described here — a feature that reads
   Shutdown differently than documented here is a bug in that feature, not a variant.
3. Where Shutdown interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Shutdown interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/operations/01_operator_guide.md`
- `docs/deployment/13_health_checks.md`

## Acceptance criteria

- [ ] Shutdown behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Shutdown contradicts a related document listed above.
- [ ] Shutdown is covered by at least one test referenced from `docs/testing/`.
- [ ] Shutdown requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Shutdown, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Shutdown that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Shutdown are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
