# Deployment Overview

> Directory: `docs/deployment/` · File: `01_deployment_overview.md` · Kind: **deployment concern**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: _(first document in this directory)_ · Next: `02_local_development.md`

## Purpose

**Deployment Overview** documents a topology or procedure for installing/running the system for "deployment overview" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Deployment Overview is a named deployment concern within the `deployment/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Deployment Overview at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Deployment Overview require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Deployment Overview is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Deployment Overview enforces the same rule set described here — a feature that reads
   Deployment Overview differently than documented here is a bug in that feature, not a variant.
3. Where Deployment Overview interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Deployment Overview interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
- `docs/deployment/01_deployment_overview.md`

## Acceptance criteria

- [ ] Deployment Overview behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Deployment Overview contradicts a related document listed above.
- [ ] Deployment Overview is covered by at least one test referenced from `docs/testing/`.
- [ ] Deployment Overview requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Deployment Overview, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Deployment Overview that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Deployment Overview are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
