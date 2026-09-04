# Latency Budgets

> Per-`runtime/11_retry_policy.md` operation class, restated here specifically as a
> performance target rather than a timeout ceiling (the timeout is the failure threshold;
> the latency budget is the target for normal operation, always well below the timeout).

| Operation class | Target (p95) | Timeout (failure threshold) | Provenance |
|---|---|---|---|
| `interactive-read` | < 200ms | 2s | CONFIG DEFAULT |
| `interactive-write` | < 500ms | 5s | CONFIG DEFAULT |
| `model-inference` (text, first token) | < 3s | 30s | DESIGN LIMIT, pending DEC-014 |
| `model-inference` (vision) | < 6s | 60s | DESIGN LIMIT, pending DEC-014 |
| `tool-lightweight` | < 100ms | 5s | CONFIG DEFAULT |
| `tool-heavyweight` | < 5s | 60s | DESIGN LIMIT (matches sandbox timeout) |
| `document-processing` (per page) | < 4s | 120s per document | DESIGN LIMIT, pending DEC-014 |
| `artifact-generation` | < 3s | 30s | CONFIG DEFAULT |

## Rule

A target is a p95, not a p50 or a hard ceiling — occasional excursions above target are
expected and are not, by themselves, a defect; sustained p95 violations are.
