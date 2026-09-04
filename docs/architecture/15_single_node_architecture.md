# Single-Node Architecture (V1)

> The concrete, demo-committed topology (DEC-001, PROFILE-B).

## Layout

All services from `15_CODEBASE_TARGET_STRUCTURE.md`'s `services/` directory run as separate
containers on one host, orchestrated by `deployment/03_docker_compose.md`, sharing:
- One PostgreSQL instance (with pgvector).
- One MinIO instance.
- One (or a small number of, if VRAM allows) local model runtime process(es).

## What single-node deliberately does not provide

No redundancy — a host failure is a full outage (`architecture/13_failure_domains.md`'s
accepted tradeoff). No horizontal scaling of any service. This is acceptable for V1's
demo/pilot-deployment target and is the explicit scope boundary from DEC-001.

## Path to multi-node

Because services are already separate containers communicating over defined APIs
(`06_service_boundaries.md`), moving to `16_multi_node_architecture.md` is a deployment
topology change (different `docker-compose`/Kubernetes manifests placing services on
different hosts) — not an application code change, provided `REQ-DEP-004` is resolved in
favor of pursuing it.
