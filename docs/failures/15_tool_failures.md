# Tool Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A ToolInvocation returns a failure result or raises an exception.

## Detection

Tool Gateway's result handling (features/05_tool_gateway/12_tool_failure_modes.md).

## System response

ToolInvocation state → `FAILED`; specific error code depends on the tool (see the tool's own failure-modes section).

## Error code

`TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Agent kernel replans (retry, substitute, or surface) per features/04_agent_kernel/10_replanning.md.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
