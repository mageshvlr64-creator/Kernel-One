# Agent Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The Agent Kernel encounters an unrecoverable error mid-task (e.g. a bug, or every replan attempt exhausted).

## Detection

Exception boundary around the AgentRun execution loop.

## System response

Task transitions to `FAILED` with a reason recorded; never left silently stuck in `EXECUTING`.

## Error code

`TOOL_EXECUTION_FAILED / INTERNAL_ERROR` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

runtime/14_resume_and_recovery.md reconciliation job catches tasks stuck beyond a grace period.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
