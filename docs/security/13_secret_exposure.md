# Secret Exposure

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A secret (JWT signing key, database credential, object storage key) is exposed via logs, error messages, or a client-visible API response.

## Where it can occur

Logging (features/25_observability/), error responses (reference/01_error_codes.md), configuration endpoints (api/23_admin_api.md).

## Mitigation

Fields marked `Secret? yes` in 16_ENVIRONMENT_AND_CONFIGURATION.md are never logged, never included in error `details`, and redacted in `GET /api/v1/admin/config` responses.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `SEC-TEST-SECRET-001 (add to testing/21_security_testing.md if not already present)`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
