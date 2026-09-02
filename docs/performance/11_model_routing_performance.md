# Model Routing Performance

> Directory: `docs/performance/` · File: `11_model_routing_performance.md` · Kind: **performance budget**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `10_document_processing_performance.md` · Next: `12_scaling_limits.md`

## Purpose

**Model Routing Performance** documents a specific latency/resource target and its consequence on breach for "model routing performance" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Model Routing Performance is a named performance budget within the `performance/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Model Routing Performance at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Model Routing Performance require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Model Routing Performance is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Model Routing Performance enforces the same rule set described here — a feature that reads
   Model Routing Performance differently than documented here is a bug in that feature, not a variant.
3. Where Model Routing Performance interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Model Routing Performance interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/performance/01_performance_requirements.md`
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`

## Acceptance criteria

- [ ] Model Routing Performance behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Model Routing Performance contradicts a related document listed above.
- [ ] Model Routing Performance is covered by at least one test referenced from `docs/testing/`.
- [ ] Model Routing Performance requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Model Routing Performance, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Model Routing Performance that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Model Routing Performance are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
