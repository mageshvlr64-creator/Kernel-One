# Authentication API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | {username, password} | {token, expires_at, user: User} | Rate class: interactive-write. On failure: `AUTH_REQUIRED` (401) after 3 attempts, `RATE_LIMITED` after 10/min. |
| `POST` | `/api/v1/auth/logout` | (none, uses Bearer token) | 204 No Content | Invalidates the current session token; emits `user.logout` audit event. |
| `GET` | `/api/v1/auth/me` | (none) | User (self) | Returns the caller's own User record, never another user's. |

## Example — POST /api/v1/auth/login

**Request:**
```
POST /api/v1/auth/login
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
