# Model Routing Performance

> Budget specific to `features/02_model_router/`'s selection decision itself, excluding the
> downstream inference call.

| Metric | Target | Provenance |
|---|---|---|
| Routing decision (capability match + policy check + resource fit) | < 50ms (p95) | CONFIG DEFAULT |
| Fallback decision (when primary model is unavailable) | < 100ms (p95) — includes the failed health check's own timeout budget | CONFIG DEFAULT |

## Why this is cheap

Routing is a lookup against the Model registry (`schemas/06_model_schema.md`) plus a policy
check (`interactive-read` class, `runtime/11_retry_policy.md`) — it does not itself involve any
model inference, which is why its budget is two orders of magnitude smaller than the
`model-inference` class it precedes.
