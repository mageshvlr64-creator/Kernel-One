# CPU Budgets

> CPU budgets per service, sized against PROFILE-B (8+ cores).

| Service | Budget (cores) | Notes |
|---|---|---|
| PostgreSQL | 2 | Vector index queries are the primary CPU consumer here |
| OCR | 2-4 (burst) | CPU-bound by nature (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` notes OCR is slow on CPU-only hardware) |
| Code Execution sandbox (per container) | 1 (enforced hard limit) | Prevents one task's code from starving others |
| API + Agent Kernel + Tool Gateway | 1-2 combined | Lightweight orchestration, not compute-heavy |
| Inference Gateway host process (excluding GPU compute) | 1 | Most compute happens on GPU; this is request handling overhead |

## Rule

Same provenance discipline as `03_memory_budgets.md` — CONFIG DEFAULT unless stated otherwise;
Code Execution's per-container CPU limit is a DESIGN LIMIT (security-motivated, not just
performance-motivated, per `features/09_code_execution/05_resource_limits.md`).
