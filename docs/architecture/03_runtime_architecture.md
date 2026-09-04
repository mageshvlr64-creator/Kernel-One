# Runtime Architecture

> How the logical layers (`02_logical_architecture.md`) actually execute: process model,
> concurrency, and request lifecycle.

## Process model (V1, single-node)

Each service in `15_CODEBASE_TARGET_STRUCTURE.md`'s `services/` directory runs as its own
container/process, communicating over the internal Docker network — even in single-node V1,
services are separate processes (not one monolith), which is what makes the service-boundary
discipline in `06_service_boundaries.md` real rather than aspirational.

## Request lifecycle (typical)

1. UI issues an HTTP/WS request to the API layer.
2. API layer authenticates, validates, and forwards to the owning service (e.g. Agent Kernel
   for a new Task).
3. The owning service calls into the trust layer (Policy Engine, Audit) synchronously — the
   request does not proceed until these calls return.
4. Long-running work (agent execution, document processing) proceeds asynchronously; the
   initiating HTTP response returns immediately with the created resource's `id` and state,
   and the client subscribes to progress via the streaming endpoint (`api/07_execution_api.md`).

## Concurrency

See `runtime/16_concurrency.md` for the specific concurrency model (per-Task serialized step
execution, but multiple Tasks execute concurrently up to the resource limits in
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`).
