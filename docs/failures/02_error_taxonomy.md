# Error Taxonomy

> How every failure in this directory maps onto the canonical error registry
> (`reference/01_error_codes.md`) and the HTTP status classes.

## Taxonomy

| Category | HTTP class | Example files in this directory | Retryable by default? |
|---|---|---|---|
| **User/input error** | 4xx (400) | `03_user_errors.md` | No |
| **Auth/authorization error** | 4xx (401/403) | `05_authentication_failures.md`, `06_authorization_failures.md`, `17_tool_permission_denied.md` | No |
| **Resource state conflict** | 4xx (404/409) | `27_citation_failures.md`, `41_approval_failures.md` | No (requires a new request, not a retry of the same one) |
| **Dependency unavailable** | 5xx (503) | `10_model_unavailable.md`, `19_database_failures.md`, `25_retrieval_failures.md`, `35_container_failures.md`, `37_storage_failures.md` | Yes, per `runtime/11_retry_policy.md` operation class |
| **Timeout** | 5xx (504) | `08_model_timeout.md`, `16_tool_timeout.md` | Depends on operation class (lightweight: yes; heavyweight: no) |
| **Resource exhaustion** | 5xx (503) | `09_model_oom.md` | Yes, via fallback routing rather than blind retry |
| **Internal/unexpected error** | 5xx (500) | Uncategorized exceptions across any component | No (unless idempotency key supplied) |
| **Configuration error** | N/A (process-level, pre-request) | `04_configuration_errors.md` | N/A — requires operator fix, not a request retry |
| **Operational failure** | N/A (not an API error) | `42_backup_failures.md`, `43_recovery_failures.md` | Per operational procedure, not the API retry policy |

## Rule

Every failure file in this directory is classified into exactly one row above, and its stated
error code must belong to that row's HTTP class in `reference/01_error_codes.md` — a mismatch
between a failure file's claimed error code and its taxonomy row is a specification defect to
fix, not a valid variance.
