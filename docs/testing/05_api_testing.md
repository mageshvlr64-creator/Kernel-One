# API Testing

> Broader than contract testing (`04_contract_testing.md`) — includes auth, rate limiting,
> pagination, and error-envelope conformance (`schemas/02_api_schema.md`) across every
> endpoint in `docs/api/`.

## Required checks per endpoint

1. Unauthenticated request → `401 AUTH_REQUIRED`.
2. Authenticated but unauthorized request (wrong role) → correct `403` variant per
   `reference/05_permission_matrix.md`.
3. Valid request → correct success shape.
4. Invalid request → `400 INVALID_REQUEST` with field-level `details`.
5. Rate limit exceeded → `429 RATE_LIMITED` with `Retry-After`.

## Automation

These five checks are parameterized once and run against every endpoint in
`reference/13_test_matrix.md`'s API section, rather than hand-written per endpoint —
consistency across ~65 routes is achieved by testing the shared envelope/auth/rate-limit
behavior generically, then adding endpoint-specific business-logic tests on top.
