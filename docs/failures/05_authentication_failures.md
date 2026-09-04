# Authentication Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Invalid credentials, expired/invalid token.

## Detection

Token validation at the API gateway layer, on every request.

## System response

`AUTH_REQUIRED` (401).

## Error code

`AUTH_REQUIRED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User re-authenticates via `POST /api/v1/auth/login`.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
