# Agent Performance

> Budgets specific to the Agent Kernel's planning/execution loop
> (`features/04_agent_kernel/`), beyond the generic `model-inference`/`tool-*` operation
> classes.

| Metric | Target | Provenance |
|---|---|---|
| Plan generation (single LLM call producing the initial Plan) | < 8s (p95) | DESIGN LIMIT, pending DEC-014 |
| Step-to-step scheduling overhead (excluding the step's own execution time) | < 100ms | CONFIG DEFAULT |
| Full task completion, simple 1-3 step task | < 15s (p95) | DESIGN LIMIT |
| Full task completion, complex task with a replan | < 60s (p95) | DESIGN LIMIT |

## Bounding mechanism

`AGENT_MAX_STEPS`/`AGENT_MAX_REPLANS` (`16_ENVIRONMENT_AND_CONFIGURATION.md`) bound worst-case
task duration regardless of the model's behavior — this is what makes the "complex task"
target above a meaningful ceiling rather than an open-ended possibility.
