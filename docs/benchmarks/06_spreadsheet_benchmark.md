# Spreadsheet Benchmark

> Directory: `docs/benchmarks/` · File: `06_spreadsheet_benchmark.md` · Kind: **benchmark**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `05_coding_benchmark.md` · Next: `07_visual_benchmark.md`

## Purpose

**Spreadsheet Benchmark** documents what is measured and how it feeds the model router for "spreadsheet benchmark" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Spreadsheet Benchmark is a named benchmark within the `benchmarks/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Spreadsheet Benchmark at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Spreadsheet Benchmark require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Spreadsheet Benchmark is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Spreadsheet Benchmark enforces the same rule set described here — a feature that reads
   Spreadsheet Benchmark differently than documented here is a bug in that feature, not a variant.
3. Where Spreadsheet Benchmark interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Spreadsheet Benchmark interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/features/02_model_router.md`
- `docs/benchmarks/01_benchmark_overview.md`

## Acceptance criteria

- [ ] Spreadsheet Benchmark behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Spreadsheet Benchmark contradicts a related document listed above.
- [ ] Spreadsheet Benchmark is covered by at least one test referenced from `docs/testing/`.
- [ ] Spreadsheet Benchmark requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Spreadsheet Benchmark, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Spreadsheet Benchmark that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Spreadsheet Benchmark are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
