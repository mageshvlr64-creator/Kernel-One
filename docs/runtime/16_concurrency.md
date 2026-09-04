# Concurrency

> How many things happen at once, and what isolates them from each other — the runtime
> realization of `performance/07_concurrency_limits.md`'s budgets and
> `architecture/13_failure_domains.md`'s isolation boundaries.

## Concurrency model

- **Across Tasks:** fully concurrent, up to the resource limits in
  `performance/07_concurrency_limits.md` — one Task's execution never blocks another's.
- **Within a single Task's Plan:** steps execute in dependency order
  (`features/04_agent_kernel/07_step_scheduler.md`); independent steps (no dependency edge
  between them) MAY execute concurrently if the scheduler chooses to (an implementation
  optimization, not a correctness requirement — sequential-within-a-task execution is always
  also correct, just potentially slower).
- **Database:** row-level locking on `UPDATE`s to shared resources (e.g. two concurrent
  approval-decision attempts on the same Approval row) — the second concurrent writer observes
  the lock and receives `RESOURCE_CONFLICT` rather than silently overwriting the first.

## Isolation

Concurrent Tasks share no mutable state except through the database (with the locking above)
and the Model Router's queue (`performance/07_concurrency_limits.md`) — there is no shared
in-memory state between concurrent Task executions that could cause one Task's bug to corrupt
another's.
