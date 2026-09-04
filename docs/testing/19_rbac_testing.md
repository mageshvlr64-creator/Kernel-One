# RBAC Testing

> Covers `features/19_identity_and_rbac/` and `features/21_policy_engine/` — the tests
> underpinning REQ-SEC-001.

## Required tests

- `SEC-TEST-002`: `Restricted User` calling a tool endpoint directly (bypassing the UI) is
  denied.
- `SEC-TEST-007`: a model-proposed tool call outside the task's authorized tool list is
  rejected before execution.
- Full role matrix coverage: for each of the six roles in `reference/06_role_matrix.md`, each
  resource/action pair in `reference/05_permission_matrix.md` behaves exactly as the matrix
  states — this is a generated/parameterized test suite covering the full grid, not a
  hand-picked sample.
