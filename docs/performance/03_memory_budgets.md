# Memory Budgets

> RAM budgets per service, sized against PROFILE-B (32GB total, `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`).

| Service | Budget | Provenance |
|---|---|---|
| PostgreSQL | 4GB (shared_buffers ~1GB, OS cache handles the rest) | CONFIG DEFAULT |
| API layer | 512MB | CONFIG DEFAULT |
| Agent Kernel | 512MB | CONFIG DEFAULT |
| Tool Gateway | 256MB | CONFIG DEFAULT |
| Code Execution sandbox (per container) | 1GB (enforced hard limit, `features/09_code_execution/05_resource_limits.md`) | DESIGN LIMIT |
| Document Ingestion + OCR | 2GB (OCR is the heavier consumer here) | CONFIG DEFAULT |
| Inference Gateway (excluding model VRAM, this is host RAM for the process itself) | 1GB | CONFIG DEFAULT |
| Remaining headroom for OS + model host-RAM overhead | ~remaining budget on a 32GB host after the above | — |

## Rule

These are per-process RSS budgets, not hard container `mem_limit` values for every service —
only Code Execution's limit is a hard enforced ceiling (since it must survive hostile input);
other services' budgets are sizing guidance for `deployment/03_docker_compose.md`'s resource
allocation, adjustable without a spec change if observed usage differs.
