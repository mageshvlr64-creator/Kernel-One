# Failure Injection

> Chaos-engineering-style deliberate failure introduction, verifying `docs/failures/`'s
> documented responses actually occur under real conditions, not just in unit-test mocks.

## Method

- Kill the database connection mid-request → verify `DEPENDENCY_UNAVAILABLE` and no partial
  write (`failures/19_database_failures.md`).
- Kill a model runtime process mid-inference → verify `MODEL_UNAVAILABLE` and fallback routing
  engages (`failures/10_model_unavailable.md`).
- Fill the backup target's disk → verify `failures/42_backup_failures.md`'s alert fires rather
  than silently succeeding with a truncated backup.
- Kill a service process mid-Task-execution → verify `runtime/14_resume_and_recovery.md`'s
  reconciliation catches the stuck task rather than leaving it silently stuck.

## Rule

Every failure file in `docs/failures/` with a "Detection" mechanism should have at least one
failure-injection test verifying that detection actually fires in a real (not mocked)
environment — this is the gap unit tests alone can't close.
