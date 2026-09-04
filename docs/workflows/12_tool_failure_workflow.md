# Tool Failure Workflow

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

features/05_tool_gateway/12_tool_failure_modes.md

## Steps

1. A ToolInvocation fails (crash, timeout, or returns an error result)
2. ToolInvocation state → FAILED or TIMEOUT per the canonical state machine
3. Agent kernel's replanning logic decides: retry (if operation class permits, runtime/11_retry_policy.md), substitute a different tool, or surface the failure to the user
4. Every failure is one AuditEvent, never silently dropped

## Notes

—
