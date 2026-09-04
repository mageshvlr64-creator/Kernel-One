# Model Registry API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/api/v1/models` | Model (minus `is_available`) | Model | Requires Administrator or Operator. Emits `model.registered`. |
| `PATCH` | `/api/v1/models/{id}` | partial Model | Model | Requires Administrator or Operator. |
| `DELETE` | `/api/v1/models/{id}` | (none) | 204 No Content | Requires Administrator. Fails with `RESOURCE_CONFLICT` if any active Task references it. |

## Example — POST /api/v1/models

**Request:**
```
POST /api/v1/models
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
