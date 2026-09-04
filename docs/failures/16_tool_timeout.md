# Tool Timeout

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A ToolInvocation exceeds its operation class timeout (tool-lightweight 5s / tool-heavyweight 60s, runtime/11_retry_policy.md).

## Detection

Gateway-side timeout timer.

## System response

ToolInvocation state → `TIMEOUT`; underlying process/container killed.

## Error code

`DEPENDENCY_UNAVAILABLE (lightweight) / SANDBOX_LIMIT_EXCEEDED (heavyweight, code execution)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Not auto-retried for tool-heavyweight (side effects may not be idempotent); agent kernel decides next step.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
