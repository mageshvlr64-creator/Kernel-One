# Permission Schema

> Directory: `docs/schemas/` · File: `14_permission_schema.md` · Kind: **schema**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `13_policy_schema.md` · Next: `15_audit_event_schema.md`

## Purpose

**Permission Schema** documents the exact on-disk/on-wire field list, types, and constraints for "permission schema" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Permission Schema is a named schema within the `schemas/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Permission Schema at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Permission Schema require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Permission Schema is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Permission Schema enforces the same rule set described here — a feature that reads
   Permission Schema differently than documented here is a bug in that feature, not a variant.
3. Where Permission Schema interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Permission Schema interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/domain/01_domain_model.md`
- `docs/api/01_api_overview.md`

## Acceptance criteria

- [ ] Permission Schema behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Permission Schema contradicts a related document listed above.
- [ ] Permission Schema is covered by at least one test referenced from `docs/testing/`.
- [ ] Permission Schema requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Permission Schema, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Permission Schema that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Permission Schema are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
