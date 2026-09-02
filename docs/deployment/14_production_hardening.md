# Production Hardening

> Directory: `docs/deployment/` · File: `14_production_hardening.md` · Kind: **deployment concern**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `13_health_checks.md` · Next: _(last document in this directory)_

## Purpose

**Production Hardening** documents a topology or procedure for installing/running the system for "production hardening" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Production Hardening is a named deployment concern within the `deployment/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Production Hardening at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Production Hardening require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Production Hardening is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Production Hardening enforces the same rule set described here — a feature that reads
   Production Hardening differently than documented here is a bug in that feature, not a variant.
3. Where Production Hardening interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Production Hardening interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
- `docs/deployment/01_deployment_overview.md`

## Acceptance criteria

- [ ] Production Hardening behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Production Hardening contradicts a related document listed above.
- [ ] Production Hardening is covered by at least one test referenced from `docs/testing/`.
- [ ] Production Hardening requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Production Hardening, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Production Hardening that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Production Hardening are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
