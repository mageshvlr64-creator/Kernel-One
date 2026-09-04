# Network Sovereignty API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/network/status` | (none) | NetworkEvent[] (`schemas/17_network_event_schema.md`), latest per check_name | Polled by `ui/13_network_panel.md` every ≤5s (REQ-NET-003). |

## Example — GET /api/v1/network/status

**Request:**
```
GET /api/v1/network/status
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
