# Agent State Schema

> Directory: `docs/schemas/` · File: `18_agent_state_schema.md` · Kind: **schema**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `17_network_event_schema.md` · Next: `19_configuration_schema.md`

## Purpose

**Agent State Schema** documents the exact on-disk/on-wire field list, types, and constraints for "agent state schema" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Agent State Schema is a named schema within the `schemas/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Agent State Schema at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Agent State Schema require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Agent State Schema is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Agent State Schema enforces the same rule set described here — a feature that reads
   Agent State Schema differently than documented here is a bug in that feature, not a variant.
3. Where Agent State Schema interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Agent State Schema interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/domain/01_domain_model.md`
- `docs/api/01_api_overview.md`

## Acceptance criteria

- [ ] Agent State Schema behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Agent State Schema contradicts a related document listed above.
- [ ] Agent State Schema is covered by at least one test referenced from `docs/testing/`.
- [ ] Agent State Schema requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Agent State Schema, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Agent State Schema that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Agent State Schema are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
