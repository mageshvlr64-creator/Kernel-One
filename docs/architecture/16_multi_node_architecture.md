# Multi-Node Architecture (V2, design-only)

> **Not built or tested for V1** — `REQ-DEP-004` in `03_REQUIREMENTS.md` is `DECISION REQUIRED`
> on whether any of this is pulled forward. This file documents the design so the V1
> architecture (`15_single_node_architecture.md`) is built compatibly with it, without
> implementing it.

## Target layout (if pursued)

- Inference Gateway replicated across multiple GPU hosts, Model Router aware of per-host
  capacity (`later/08_multi_node_scaling.md`).
- PostgreSQL with read replicas for `interactive-read` load; writes still go to a single
  primary (no multi-primary in the initial multi-node design, to avoid the correctness
  complexity of distributed writes for an audit-critical system).
- Object storage already S3-compatible (DEC-003), so scaling it is largely infrastructure
  configuration, not application change.

## What must NOT change when this is eventually built

Every trust-layer invariant (`security/25_security_invariants.md`) must hold identically in a
multi-node deployment — network sovereignty enforcement, audit append-only guarantees, and
authorization checks are not weakened by distribution, per the same principle stated in
`security/03_trust_model.md`'s note about internal service-to-service trust.
