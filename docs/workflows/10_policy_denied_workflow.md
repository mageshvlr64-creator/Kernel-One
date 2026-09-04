# Policy-Denied Workflow

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

REQ-SEC-001

## Steps

1. User/agent attempts an action the policy engine denies (e.g. Restricted User invoking code execution)
2. API returns POLICY_DENIED or TOOL_NOT_ALLOWED (reference/01_error_codes.md) before any state change
3. AuditEvent recorded with decision=denied
4. UI shows the exact user-visible message from the error registry, never a generic failure

## Notes

Demonstrated live in demo/01_demo_overview.md step 12.
