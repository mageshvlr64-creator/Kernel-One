# Model Failure / Fallback Workflow

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

features/02_model_router/09_fallback_routing.md

## Steps

1. Primary model becomes unreachable (health check fails)
2. Circuit breaker opens for that model (runtime/11_retry_policy.md, model-inference class)
3. Router selects the configured fallback model for the same capability slot
4. If no fallback is configured/available, MODEL_UNAVAILABLE is returned and the task transitions per its replanning/failure rules

## Notes

Demonstrated in demo/01_demo_overview.md secondary scenarios.
