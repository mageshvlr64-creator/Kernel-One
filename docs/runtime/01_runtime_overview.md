# Runtime Overview

> Index for `docs/runtime/`. State machines live in `_state_machines_canonical.md`
> (referenced by the `04..09_*_state_machine.md` pointer files); this directory's remaining
> files cover lifecycle, timing, and concurrency behavior not captured by the state tables
> alone.

## Contents

| File | Covers |
|---|---|
| `_state_machines_canonical.md` | Task, ToolInvocation, Approval, Artifact, Document state machines |
| `02_task_lifecycle.md`, `03_execution_lifecycle.md` | Narrative lifecycle walkthroughs (the state machine is the formal spec; these are the readable version) |
| `10_model_request_lifecycle.md` | A single inference call's lifecycle |
| `11_retry_policy.md` | Canonical retry/timeout/backoff table (already complete) |
| `12_timeout_policy.md` | Restates the timeout half of `11_retry_policy.md` with cleanup-on-timeout detail |
| `13_cancellation_policy.md` | User-initiated cancellation behavior |
| `14_resume_and_recovery.md` | What happens after a service restart mid-task |
| `15_idempotency.md` | Which operations are safely retryable and how |
| `16_concurrency.md` | How many things can happen at once, and isolation between them |
| `17_queueing.md`, `18_backpressure.md` | What happens when a resource limit is reached |
| `19_runtime_invariants.md` | The "always true" statements this directory assumes |
