# Sandbox Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The code execution container fails to start, or exits abnormally not covered by timeout/resource-limit files.

## Detection

Container orchestration layer's error handling (features/09_code_execution/).

## System response

ToolInvocation → `FAILED`, with the container's exit code/stderr captured for the user.

## Error code

`TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Not auto-retried (side effects may not be idempotent, DEC-005); user reviews the error output.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
