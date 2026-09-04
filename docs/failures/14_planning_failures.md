# Planning Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The Agent Kernel cannot produce a valid Plan (e.g. the model's proposed plan fails schema validation, or requests a tool that doesn't exist).

## Detection

Plan validation step (features/04_agent_kernel/05_plan_validation.md) before any step executes.

## System response

Task fails at the `PLANNING` state, never silently substitutes an unvalidated plan.

## Error code

`INVALID_REQUEST (internal) / TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Agent kernel retries planning once with a corrective prompt; if still invalid, surfaces to the user.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
