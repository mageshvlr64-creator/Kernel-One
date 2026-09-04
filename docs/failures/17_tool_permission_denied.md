# Tool Permission Denied

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Caller's role/policy doesn't authorize the requested tool.

## Detection

Tool Gateway authorization check (features/05_tool_gateway/04_tool_permissions.md), before invocation.

## System response

`TOOL_NOT_ALLOWED` (403); ToolInvocation never reaches `AUTHORIZED` state.

## Error code

`TOOL_NOT_ALLOWED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Not automatically recoverable — requires a role/policy change (by design, REQ-SEC-001).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
