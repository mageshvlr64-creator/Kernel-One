# Tools API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/tools` | (none) | Tool[] | Filtered to tools the caller's role may invoke, per `reference/05_permission_matrix.md`. |
| `POST` | `/api/v1/tools/{tool_id}/invoke` | ToolInvocationRequest (`schemas/05_tool_call_schema.md`) | ToolInvocationResult | Primarily called by the agent kernel; direct calls audited identically. `403 TOOL_NOT_ALLOWED` on denial. |

## Example — GET /api/v1/tools

**Request:**
```
GET /api/v1/tools
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
