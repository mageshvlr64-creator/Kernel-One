# Error Contracts

> This file does not redefine error codes — the canonical registry is
> `docs/reference/01_error_codes.md`. This file defines only the HTTP-layer *shape* every
> error takes, which is identical across all endpoints.

## Shape

Every non-2xx response body matches `ApiErrorEnvelope` in `docs/schemas/02_api_schema.md`:

```json
{
  "error": {
    "code": "POLICY_DENIED",
    "message": "You don't have permission to do this.",
    "details": null,
    "correlation_id": "5b9c9e3a-4b0a-4c9f-9a1b-1e2f3a4b5c6d"
  }
}
```

## Rules

1. `code` is always one of `docs/reference/01_error_codes.md` — never a free-text string, and
   never an endpoint-specific code invented locally.
2. `message` is always the exact "User message" column value from the registry for that code —
   endpoints do not write their own error copy.
3. `details` is populated only for `INVALID_REQUEST`, containing field-level validation errors:
   `{"field_errors": [{"field": "classification", "message": "must be one of PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED"}]}`.
4. `correlation_id` is always present and matches the `correlation_id` on the corresponding
   `AuditEvent` (`schemas/15_audit_event_schema.md`), so an operator can go from a user-reported
   error straight to the exact audit trail.
5. HTTP status code always matches the registry's "HTTP" column for that `code` — an endpoint
   never overrides it.
