# API Envelope Schema (Canonical)

> Canonical request/response envelope and error shape used by every endpoint in `docs/api/`.
> Individual endpoints reference this file for the envelope and their own entity schema
> (`docs/schemas/03_task_schema.md` etc.) for the payload — they do not redefine either.

## Success envelope

```json
{
  "$id": "api-success-envelope.json",
  "title": "ApiSuccessEnvelope",
  "type": "object",
  "required": ["data"],
  "properties": {
    "data": { "description": "Endpoint-specific payload; see the matching docs/schemas/ file" },
    "pagination": {
      "type": "object",
      "properties": {
        "next_cursor": { "type": ["string", "null"] },
        "limit": { "type": "integer" }
      }
    }
  }
}
```

## Error envelope

```json
{
  "$id": "api-error-envelope.json",
  "title": "ApiErrorEnvelope",
  "type": "object",
  "required": ["error"],
  "properties": {
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "description": "One of docs/reference/01_error_codes.md" },
        "message": { "type": "string", "description": "User-visible message from the registry" },
        "details": { "type": ["object", "null"], "description": "Field-level validation errors, present only for INVALID_REQUEST" },
        "correlation_id": { "type": "string", "format": "uuid" }
      }
    }
  }
}
```

## Conventions

- All endpoints are versioned under `/api/v1/`.
- All state-changing endpoints accept an optional `Idempotency-Key` header; behavior when
  supplied is defined per-endpoint in `docs/api/`, defaulting to "safe to retry with the same
  key returns the original result" for endpoints marked idempotent in `docs/runtime/15_idempotency.md`.
- Pagination: cursor-based (`?cursor=...&limit=...`), default `limit=50`, max `limit=200`.
- Filtering/sorting: `?filter[field]=value`, `?sort=field` / `?sort=-field` (descending).
- Streaming endpoints (inference) use Server-Sent Events; see `docs/api/07_execution_api.md`
  and `docs/features/03_inference_gateway/07_streaming.md`.
- Rate limits: `interactive-read`/`interactive-write` operation classes are limited per-user
  at 60 requests/minute (CONFIG DEFAULT); exceeding this returns `429 RATE_LIMITED` with a `Retry-After`
  header, per `docs/reference/01_error_codes.md`.
