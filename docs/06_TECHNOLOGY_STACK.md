# Technology Stack

> Root specification document · `docs/06_TECHNOLOGY_STACK.md`
> Previous: `05_ARCHITECTURAL_PRINCIPLES.md` · Next: `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`

## Purpose

The single authoritative table of what this system is built from. If a technology choice
isn't in this table, it isn't decided — see `20_DECISION_LOG.md` for the reasoning behind
each row, and `integrations/*.md` for how each is actually wrapped in code. This document
does not restate that reasoning, it assembles the conclusions into one place so nobody has to
cross-reference sixteen files to answer "what does this system run on."

## Stack table

| Layer | Technology | MVP status | Rationale (full detail) |
|---|---|---|---|
| Frontend | React (`apps/workbench-ui/`) | MUST IMPLEMENT | `15_CODEBASE_TARGET_STRUCTURE.md` |
| Backend services | Python (adapters and services under `services/*`) | MUST IMPLEMENT | `integrations/02_vllm.md` (`adapters/vllm.py`) and sibling adapter files |
| Database (relational + vector) | PostgreSQL 15+ with `pgvector` (HNSW index) and `pgcrypto` | MUST IMPLEMENT | DEC-002, `integrations/05_postgresql.md`, `06_pgvector.md` |
| Object storage | MinIO (S3-compatible API) | MUST IMPLEMENT | DEC-003, `integrations/07_minio.md` |
| Local inference — primary | vLLM (OpenAI-compatible HTTP API), GPU-resident | MUST IMPLEMENT | DEC-004, `integrations/02_vllm.md` |
| Local inference — fallback | Ollama (quick local iteration, PROFILE-A / lower-VRAM) | MUST IMPLEMENT | DEC-004, `integrations/03_ollama.md` |
| Local inference — CPU fallback | llama.cpp (`llama-server`, OpenAI-compatible) | MUST IMPLEMENT | DEC-004, `integrations/04_llamacpp.md`, `deployment/06_cpu_only_demo.md` |
| Agent runtime | Custom agent kernel (`services/agent-kernel/`) — not a third-party framework | MUST IMPLEMENT | `features/04_agent_kernel/`, chosen so plan/execute/verify/replan stays under this spec's exact control rather than a framework's assumptions |
| OCR | PaddleOCR | MUST IMPLEMENT | `integrations/08_paddleocr.md` — CPU-only accuracy sufficient without requiring a GPU, per REQ-AI-002 |
| PDF parsing | PyMuPDF | MUST IMPLEMENT | `integrations/09_pymupdf.md` |
| Office document conversion | LibreOffice (headless) | MUST IMPLEMENT | `integrations/10_libreoffice.md` |
| Sandbox / container runtime | Docker (service deployment) + Firejail (code-execution sandbox) | MUST IMPLEMENT | DEC-005, `integrations/11_docker.md` |
| Auth (V1) | Direct authentication against the local `users` table — no external IdP | MUST IMPLEMENT | `features/19_identity_and_rbac/02_authentication.md` |
| Auth (V2, not V1) | Keycloak | FUTURE | `integrations/12_keycloak.md`, `later/10_enterprise_identity_integration.md` |
| Tracing / metrics instrumentation | OpenTelemetry | MUST IMPLEMENT | `integrations/13_opentelemetry.md`, `features/25_observability/` |
| Metrics backend | Prometheus | MUST IMPLEMENT | `integrations/14_prometheus.md` |
| Dashboards | Grafana | MUST IMPLEMENT | `integrations/15_grafana.md` |
| Keyword search | PostgreSQL full-text search (`tsvector`/`tsquery`), combined with `pgvector` for hybrid retrieval | MUST IMPLEMENT | Same database as the relational store (DEC-002) — no separate search engine (e.g. Elasticsearch/OpenSearch) is used in V1, to keep the single-node deployment true to `architecture/15_single_node_architecture.md` |
| Reverse proxy | **Not yet decided** | OPEN | No file in this tree names one. `deployment/03_docker_compose.md` and `architecture/*` do not specify how inbound traffic is terminated/routed in front of the API layer. This should be resolved with a `20_DECISION_LOG.md` entry (a reasonable default would be Nginx or Traefik, but naming one here without that decision being made would be inventing a choice this audit was told not to make) |
| Cache / queue | **Not yet decided** | OPEN | No file names a cache or message-queue technology. `features/04_agent_kernel/` and `features/22_agent_memory/` may need one for task-step state or session caching, but nothing in the current tree specifies it. Same resolution path as Reverse Proxy above |

## Deployment modes this stack must support without code changes

Air-gapped, restricted-network, and connected-on-premise — see
`architecture/17-19_*.md` and `16_ENVIRONMENT_AND_CONFIGURATION.md`. Every row above marked
MUST IMPLEMENT is expected to run correctly in all three modes; none of them depend on
outbound internet access for core operation, per `05_ARCHITECTURAL_PRINCIPLES.md` principle 1.

## Explicitly not used in V1

- **Keycloak** — deferred to V2, see row above.
- **A dedicated vector database** (e.g. Milvus, Qdrant, Weaviate) — rejected in favor of
  `pgvector` per DEC-002, to avoid a second database to operate and back up in a single-node
  V1 deployment.
- **A dedicated search engine** (Elasticsearch/OpenSearch) — rejected in favor of PostgreSQL
  full-text search for the same single-node reason.
- **Kubernetes** — V1 targets `deployment/03_docker_compose.md`; Kubernetes is a `later/`
  item, see DEC-015/016 (open) in `20_DECISION_LOG.md`.

## Open items

The two OPEN rows above (Reverse Proxy, Cache/Queue) should be resolved with dated
`20_DECISION_LOG.md` entries before implementation reaches the services that need them —
tracked as a known gap rather than silently assumed.

## Related documents

- `docs/20_DECISION_LOG.md` — DEC-001 through DEC-007 for the full reasoning behind each MUST
  IMPLEMENT row above.
- `docs/integrations/*.md` — the per-technology integration contract.
- `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` — what hardware this stack must run on.

## Maintenance

Any change to a row in the stack table above must be accompanied by a new `20_DECISION_LOG.md`
entry and, where applicable, a corresponding `integrations/*.md` file.
