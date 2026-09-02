# Security Incidents

> Directory: `docs/operations/` · File: `11_security_incidents.md` · Kind: **operator procedure**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `10_incident_response.md` · Next: `12_network_incidents.md`

## Purpose

**Security Incidents** documents a day-to-day runbook step for a human operator for "security incidents" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Security Incidents is a named operator procedure within the `operations/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Security Incidents at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Security Incidents require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Security Incidents is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Security Incidents enforces the same rule set described here — a feature that reads
   Security Incidents differently than documented here is a bug in that feature, not a variant.
3. Where Security Incidents interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Security Incidents interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/operations/01_operator_guide.md`
- `docs/deployment/13_health_checks.md`

## Acceptance criteria

- [ ] Security Incidents behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Security Incidents contradicts a related document listed above.
- [ ] Security Incidents is covered by at least one test referenced from `docs/testing/`.
- [ ] Security Incidents requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Security Incidents, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Security Incidents that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Security Incidents are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
