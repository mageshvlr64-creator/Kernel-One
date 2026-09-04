# Resume and Recovery

> What happens when a service restarts (planned or crash) while Tasks are mid-execution —
> referenced by `failures/13_agent_failures.md` and `workflows/13_recovery_workflow.md`.

## Mechanism

Every state transition is committed to the database *after* its side effect completes, not
before (`_state_machines_canonical.md`'s general convention) — so a crash mid-transition
leaves the Task in its last successfully-committed state, never in a state implying work that
didn't actually happen.

## Reconciliation job

On service startup (`operations/02_startup.md`), a reconciliation job queries for Tasks stuck
in `EXECUTING` or `PLANNING` beyond a grace period (CONFIG DEFAULT: 5 minutes past their last
update) and either:
1. Resumes execution if the AgentRun's Plan is still valid and the failed step can be safely
   re-attempted (per `15_idempotency.md`'s idempotency rules for that step's tool), or
2. Transitions the Task to `FAILED` with a "recovery timeout" reason, if resumption isn't
   safely possible — never leaves it silently stuck indefinitely.

## Rule

A user should never see a Task permanently stuck in a non-terminal state with no eventual
resolution — the reconciliation job's grace period is the upper bound on how long "stuck" can
persist before the system takes a definitive action.
