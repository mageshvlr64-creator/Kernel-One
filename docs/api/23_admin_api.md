# Admin API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/admin/health` | (none) | {status: 'healthy'|'degraded'|'unhealthy', components: {...}} | See `24_health_api.md` for the full health-check contract. |
| `GET` | `/api/v1/admin/config` | (none) | ConfigurationEntry[] (`schemas/19_configuration_schema.md`), secrets redacted | Requires Administrator. |

## Example — GET /api/v1/admin/health

**Request:**
```
GET /api/v1/admin/health
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
