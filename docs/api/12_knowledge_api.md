# Knowledge / Indexing API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/documents/{id}/chunks` | query: ?cursor&limit | paginated DocumentChunk[] (`schemas/08_chunk_schema.md`) | Requires same clearance check as the parent document. |
| `POST` | `/api/v1/documents/{id}/reindex` | (none) | Document (state→INDEXING) | Requires Administrator/Operator; used after an embedding-model change. |

## Example — GET /api/v1/documents/{id}/chunks

**Request:**
```
GET /api/v1/documents/{id}/chunks
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
