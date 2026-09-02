# Tool Use Benchmark

> Directory: `docs/benchmarks/` · File: `08_tool_use_benchmark.md` · Kind: **benchmark**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `07_visual_benchmark.md` · Next: `09_citation_benchmark.md`

## Purpose

**Tool Use Benchmark** documents what is measured and how it feeds the model router for "tool use benchmark" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Tool Use Benchmark is a named benchmark within the `benchmarks/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Tool Use Benchmark at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Tool Use Benchmark require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Tool Use Benchmark is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Tool Use Benchmark enforces the same rule set described here — a feature that reads
   Tool Use Benchmark differently than documented here is a bug in that feature, not a variant.
3. Where Tool Use Benchmark interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Tool Use Benchmark interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/features/02_model_router.md`
- `docs/benchmarks/01_benchmark_overview.md`

## Acceptance criteria

- [ ] Tool Use Benchmark behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Tool Use Benchmark contradicts a related document listed above.
- [ ] Tool Use Benchmark is covered by at least one test referenced from `docs/testing/`.
- [ ] Tool Use Benchmark requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Tool Use Benchmark, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Tool Use Benchmark that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Tool Use Benchmark are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
