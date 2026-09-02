# Concurrency Limits

> Directory: `docs/performance/` · File: `07_concurrency_limits.md` · Kind: **performance budget**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `06_storage_budgets.md` · Next: `08_agent_performance.md`

## Purpose

**Concurrency Limits** documents a specific latency/resource target and its consequence on breach for "concurrency limits" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Concurrency Limits is a named performance budget within the `performance/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Concurrency Limits at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Concurrency Limits require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Concurrency Limits is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Concurrency Limits enforces the same rule set described here — a feature that reads
   Concurrency Limits differently than documented here is a bug in that feature, not a variant.
3. Where Concurrency Limits interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Concurrency Limits interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/performance/01_performance_requirements.md`
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`

## Acceptance criteria

- [ ] Concurrency Limits behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Concurrency Limits contradicts a related document listed above.
- [ ] Concurrency Limits is covered by at least one test referenced from `docs/testing/`.
- [ ] Concurrency Limits requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Concurrency Limits, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Concurrency Limits that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Concurrency Limits are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
