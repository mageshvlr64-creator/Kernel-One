# Documents API

> Concrete endpoint contract. All endpoints are versioned under `/api/v1/` unless noted,
> authenticated via Bearer token (`02_authentication_api.md`) unless noted, and use the
> envelope defined in `docs/schemas/02_api_schema.md`. Errors are always one of
> `docs/reference/01_error_codes.md`.

## Endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/api/v1/documents` | multipart: file + {workspace_id, classification} | Document (`schemas/07_document_schema.md`), state=UPLOADED | Requires `Document:create`; size ≤ 200MB or `INVALID_REQUEST`. |
| `GET` | `/api/v1/documents/{id}` | (none) | Document | `FILE_CLASSIFICATION_DENIED` if caller clearance < document classification. |
| `GET` | `/api/v1/documents` | query: ?workspace_id&state&cursor&limit | paginated Document[] | Classification-filtered per caller clearance. |
| `DELETE` | `/api/v1/documents/{id}` | (none) | 204 No Content | Soft-delete; requires ownership or Administrator. |

## Example — POST /api/v1/documents

**Request:**
```
POST /api/v1/documents
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
