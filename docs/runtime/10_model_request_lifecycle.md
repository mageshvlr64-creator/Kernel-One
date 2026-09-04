# Model Request Lifecycle

> The lifecycle of a single inference call through the Inference Gateway
> (`features/03_inference_gateway/`) — narrower in scope than the Task/ToolInvocation state
> machines since a model request isn't itself a persisted entity with its own state column
> (it's tracked implicitly via the `Message.model_id` field and, if it fails, a
> `failures/07_model_failures.md`-class event).

## Lifecycle

1. Model Router selects a model for the request's capability + classification
   (`features/02_model_router/`), per its own `<50ms` budget
   (`performance/11_model_routing_performance.md`).
2. Inference Gateway forwards the request to the selected provider adapter
   (`integrations/02..04_*.md`).
3. Response streams back (`features/03_inference_gateway/07_streaming.md`) or returns whole,
   depending on the endpoint (`api/07_execution_api.md`).
4. On success, the response is validated against the expected schema before being used
   (malformed responses are treated as `failures/07_model_failures.md`, not passed through).
5. On failure at any step, the circuit-breaker/fallback logic in `11_retry_policy.md` and
   `features/02_model_router/09_fallback_routing.md` engages.

## No independent persistence

Unlike Task/ToolInvocation, an individual model request's intermediate states aren't
separately queryable via the API — only its outcome (the resulting Message, or a surfaced
error) is persisted, keeping this lifecycle lightweight relative to the entity-backed state
machines.
