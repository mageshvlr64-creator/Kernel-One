# Tool State Machine

> Directory: `docs/runtime/` · File: `06_tool_state_machine.md` · Kind: **runtime rule**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `05_execution_state_machine.md` · Next: `07_approval_state_machine.md`

## Purpose

**Tool State Machine** documents lifecycle, state-machine, or concurrency behavior for "tool state machine" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Tool State Machine is a named runtime rule within the `runtime/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Tool State Machine at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Tool State Machine require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Tool State Machine is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Tool State Machine enforces the same rule set described here — a feature that reads
   Tool State Machine differently than documented here is a bug in that feature, not a variant.
3. Where Tool State Machine interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Tool State Machine interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/failures/01_failure_handling_philosophy.md`

## Acceptance criteria

- [ ] Tool State Machine behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Tool State Machine contradicts a related document listed above.
- [ ] Tool State Machine is covered by at least one test referenced from `docs/testing/`.
- [ ] Tool State Machine requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Tool State Machine, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Tool State Machine that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Tool State Machine are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
