# Tasks API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/api/v1/tasks` | TaskRequest (`schemas/03_task_schema.md`) | Task | Requires `Task:create`. Initial state `CREATED`. Emits `task.created`. |
| `GET` | `/api/v1/tasks/{id}` | (none) | Task | Requires `Task:read` (own, or any in workspace for Administrator/Operator/SecurityOfficer). |
| `GET` | `/api/v1/tasks` | query: ?workspace_id&state&cursor&limit | paginated Task[] | — |
| `POST` | `/api/v1/tasks/{id}/cancel` | (none) | Task (state=CANCELLED) | Requires `Task:delete` or ownership. Emits `task.cancelled`. |

## Example — POST /api/v1/tasks

**Request:**
```
POST /api/v1/tasks
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
