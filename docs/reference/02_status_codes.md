# HTTP Status Codes (Reference)

> This file maps HTTP status codes to their meaning in this system specifically — the
> authoritative per-error mapping is `01_error_codes.md`; this file is the reverse index
> (status code → which errors use it) for quick lookup.

| Status | Meaning here | Error codes using it |
|---|---|---|
| 200 | Success | — |
| 204 | Success, no body (deletes, logout) | — |
| 400 | Client sent an invalid request | `INVALID_REQUEST` |
| 401 | Not authenticated | `AUTH_REQUIRED` |
| 403 | Authenticated but not authorized | `POLICY_DENIED`, `TOOL_NOT_ALLOWED`, `FILE_CLASSIFICATION_DENIED`, `APPROVAL_REQUIRED`, `APPROVAL_REJECTED`, `NETWORK_EGRESS_BLOCKED`, `MODEL_NOT_APPROVED` |
| 404 | Resource not found or not visible to caller | `FILE_NOT_FOUND` |
| 409 | State conflict | `RESOURCE_CONFLICT` |
| 429 | Rate limited | `RATE_LIMITED` |
| 500 | Internal error | `INTERNAL_ERROR`, `TOOL_EXECUTION_FAILED`, `SANDBOX_LIMIT_EXCEEDED` |
| 503 | Dependency unavailable | `MODEL_UNAVAILABLE`, `MODEL_RESOURCE_EXHAUSTED`, `RAG_INDEX_UNAVAILABLE`, `DEPENDENCY_UNAVAILABLE` |
| 504 | Dependency timeout | `INFERENCE_TIMEOUT` |

## Rule

A given error code always returns the same status code everywhere in the system — an
endpoint never overrides this mapping (`api/26_error_contracts.md` rule 5).
