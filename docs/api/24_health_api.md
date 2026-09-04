# Health API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/healthz` | (none) | 200 if process is up (liveness) | No auth required; used by container orchestrator liveness probe. |
| `GET` | `/readyz` | (none) | 200 if DB/object-storage/model-runtime dependencies are reachable (readiness) | No auth required; used by readiness probe — see `deployment/13_health_checks.md`. |

## Example — GET /healthz

**Request:**
```
GET /healthz
Authorization: Bearer <token>
Content-Type: application/json

{}
```

**Response `200 OK`:**
```json
{
  "data": { "...": "see linked schema for exact fields" }
}
```

**Response `403`** (if the caller's role/policy denies this action):
```json
{
  "error": {
    "code": "POLICY_DENIED",
    "message": "You don't have permission to do this.",
    "correlation_id": "5b9c9e3a-4b0a-4c9f-9a1b-1e2f3a4b5c6d"
  }
}
```
