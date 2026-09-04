# Agent Testing

> Covers `features/04_agent_kernel/` specifically: planning, step scheduling, replanning, and
> the full plan-to-completion loop.

## Required tests

- Given a fixed prompt and a mocked model response producing a specific Plan, the scheduler
  executes steps in the declared dependency order (`schemas/04_execution_schema.md`).
- A step failure triggers replanning, capped at `AGENT_MAX_REPLANS`
  (`16_ENVIRONMENT_AND_CONFIGURATION.md`) — the (N+1)th failure surfaces to the user rather
  than replanning indefinitely.
- A plan exceeding `AGENT_MAX_STEPS` is rejected at validation, never partially executed then
  cut off mid-step.

## Determinism note

Since model output is not deterministic, these tests mock the model's plan-generation
response rather than relying on a real model call — real-model behavior is covered by
`TEST-E2E-002` (`demo/06_coding_agent_demo.md`), which accepts some output variance by
checking outcome (task completes, artifact produced) rather than exact plan content.
