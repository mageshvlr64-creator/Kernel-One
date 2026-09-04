# Tool Testing

> Covers `features/05_tool_gateway/` and each individual tool (`06_filesystem_tool/` through
> `09_code_execution/`).

## Required tests per tool

- Authorized invocation succeeds and produces the documented output shape.
- Unauthorized invocation (wrong role) → `TOOL_NOT_ALLOWED`, `SEC-TEST-002`/`007`.
- Tool-specific security test where applicable: `SEC-TEST-003` (code execution network
  denial), `SEC-TEST-005` (filesystem path traversal).
- Timeout: a tool call exceeding its operation class timeout (`runtime/11_retry_policy.md`)
  is killed and returns the correct error code.
