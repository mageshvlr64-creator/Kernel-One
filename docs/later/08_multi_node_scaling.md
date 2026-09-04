# Multi-Node Scaling (V2+)

> The production realization of `architecture/16_multi_node_architecture.md`, currently a
> design document only (DEC-001). See `REQ-DEP-004` in `03_REQUIREMENTS.md` — marked
> **DECISION REQUIRED** as to whether any of this is pulled into V1.

## What V1's single-node design already provides for this transition

Per DEC-001, services are already separated by clear API boundaries
(`architecture/06_service_boundaries.md`) specifically so this migration doesn't require a
rewrite — this is the concrete payoff of that V1 architectural choice.

## What multi-node adds

- Horizontal scaling of the Inference Gateway across multiple GPU hosts, with the Model Router
  aware of per-host capacity (extends `features/02_model_router/05_resource_fit.md`).
- A distributed task queue instead of in-process scheduling for the Agent Kernel
  (`runtime/17_queueing.md` would need a concrete backend chosen — e.g. a message broker —
  which is currently unspecified for V1's single-node case).
- Database read replicas for `interactive-read` operation class load (`runtime/11_retry_policy.md`).

## Prerequisite decision

`REQ-PERF-002` (target concurrent user count, also `DECISION REQUIRED`) must be answered before
multi-node design work is justified — if V1's actual target concurrency fits comfortably on
PROFILE-C single-node, this entire item may remain deferred indefinitely rather than becoming
active V2 work.
