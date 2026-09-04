# RBAC API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/rbac/matrix` | (none) | the static permission matrix as JSON (mirrors `reference/05_permission_matrix.md`) | Read-only; the matrix itself is not editable via API in V1 (fixed six-role model, DEC-006). |
| `POST` | `/api/v1/rbac/check` | PermissionCheckRequest (`schemas/14_permission_schema.md`) | PermissionCheckResult | Used by UI to pre-emptively hide disallowed actions; the server-side check on the actual action endpoint is still authoritative. |

## Example — GET /api/v1/rbac/matrix

**Request:**
```
GET /api/v1/rbac/matrix
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
