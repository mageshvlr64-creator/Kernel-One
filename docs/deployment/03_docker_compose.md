# Docker Compose

> Directory: `docs/deployment/` · File: `03_docker_compose.md` · Kind: **deployment concern**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `02_local_development.md` · Next: `04_single_server.md`

## Purpose

**Docker Compose** documents a topology or procedure for installing/running the system for "docker compose" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Docker Compose is a named deployment concern within the `deployment/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Docker Compose at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Docker Compose require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Docker Compose is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Docker Compose enforces the same rule set described here — a feature that reads
   Docker Compose differently than documented here is a bug in that feature, not a variant.
3. Where Docker Compose interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Docker Compose interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
- `docs/deployment/01_deployment_overview.md`

## Acceptance criteria

- [ ] Docker Compose behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Docker Compose contradicts a related document listed above.
- [ ] Docker Compose is covered by at least one test referenced from `docs/testing/`.
- [ ] Docker Compose requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Docker Compose, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Docker Compose that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Docker Compose are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
