# Users API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/users` | query: ?cursor&limit | paginated User[] | Requires `User:read`; Administrator/Auditor only per `reference/05_permission_matrix.md`. |
| `POST` | `/api/v1/users` | {username, display_name, password, role, clearance} | User | Requires `User:create` (Administrator only). Emits `user.created`. |
| `PATCH` | `/api/v1/users/{id}` | {display_name?, role?, clearance?, is_active?} | User | Requires `User:update` (Administrator only). |
| `DELETE` | `/api/v1/users/{id}` | (none) | 204 No Content | Sets `is_active=false`; never a hard delete (audit-trail continuity). |

## Example — GET /api/v1/users

**Request:**
```
GET /api/v1/users
Authorization: Bearer <token>
Content-Type: application/json

{ ... see request schema ... }
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
