# Upgrade Procedure

> Directory: `docs/deployment/` · File: `11_upgrade_procedure.md` · Kind: **deployment concern**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `10_backup_deployment.md` · Next: `12_rollback_procedure.md`

## Purpose

**Upgrade Procedure** documents a topology or procedure for installing/running the system for "upgrade procedure" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Upgrade Procedure is a named deployment concern within the `deployment/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Upgrade Procedure at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Upgrade Procedure require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Upgrade Procedure is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Upgrade Procedure enforces the same rule set described here — a feature that reads
   Upgrade Procedure differently than documented here is a bug in that feature, not a variant.
3. Where Upgrade Procedure interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Upgrade Procedure interacts with risk or exposure, treat it as **medium**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
- `docs/deployment/01_deployment_overview.md`

## Acceptance criteria

- [ ] Upgrade Procedure behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Upgrade Procedure contradicts a related document listed above.
- [ ] Upgrade Procedure is covered by at least one test referenced from `docs/testing/`.
- [ ] Upgrade Procedure requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Upgrade Procedure, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Upgrade Procedure that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Upgrade Procedure are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
