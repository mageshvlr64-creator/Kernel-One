# Search / RAG API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/api/v1/search` | {workspace_id, query, top_k?} | {results: DocumentChunk[], method: 'vector'|'keyword'|'hybrid'} | Classification/workspace filter applied at query time (REQ-FUNC-004), not post-filtered. |

## Example — POST /api/v1/search

**Request:**
```
POST /api/v1/search
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
