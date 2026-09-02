# Network Incidents

> Directory: `docs/operations/` · File: `12_network_incidents.md` · Kind: **operator procedure**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `11_security_incidents.md` · Next: `13_disaster_recovery.md`

## Purpose

**Network Incidents** documents a day-to-day runbook step for a human operator for "network incidents" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Network Incidents is a named operator procedure within the `operations/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Network Incidents at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Network Incidents require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Network Incidents is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Network Incidents enforces the same rule set described here — a feature that reads
   Network Incidents differently than documented here is a bug in that feature, not a variant.
3. Where Network Incidents interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Network Incidents interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/operations/01_operator_guide.md`
- `docs/deployment/13_health_checks.md`

## Acceptance criteria

- [ ] Network Incidents behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Network Incidents contradicts a related document listed above.
- [ ] Network Incidents is covered by at least one test referenced from `docs/testing/`.
- [ ] Network Incidents requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Network Incidents, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Network Incidents that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Network Incidents are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
