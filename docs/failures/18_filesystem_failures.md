# Filesystem Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Path traversal attempt, file not found, size limit exceeded, or disk I/O error.

## Detection

Filesystem Tool's path validation and I/O error handling (features/06_filesystem_tool/).

## System response

`INVALID_REQUEST` (traversal attempt), `FILE_NOT_FOUND`, or `DEPENDENCY_UNAVAILABLE` (disk I/O error).

## Error code

`INVALID_REQUEST / FILE_NOT_FOUND / DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Traversal attempts are logged as security-relevant (security/09_path_traversal.md), not merely retried.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
