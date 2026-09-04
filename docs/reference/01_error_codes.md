# Error Registry (Canonical)

> **Canonical owner** of every error code in the system. Feature documents MUST reference an
> error code from this table by name; they MUST NOT invent a new code inline. If a feature
> needs an error not listed here, add it here first, in the same change.

## Format

`ERROR_CODE` · HTTP status · Category · Meaning · Retryable · User-visible message ·
Operator detail · Remediation · Audit requirement.

## Registry

| Error code | HTTP | Category | Meaning | Retryable | User message | Operator detail | Remediation | Audit? |
|---|---|---|---|---|---|---|---|---|
| `INVALID_REQUEST` | 400 | Validation | Request body/params failed schema validation | No | "Your request couldn't be processed — check the highlighted fields." | Field-level validation errors from the schema validator | Fix request per schema in `docs/schemas/` | Yes |
| `AUTH_REQUIRED` | 401 | Auth | No valid session/token presented | No | "Please sign in to continue." | Missing/expired bearer token | Re-authenticate | Yes |
| `POLICY_DENIED` | 403 | AuthZ | Policy engine denied the action for this actor/resource/action combination | No | "You don't have permission to do this." | Denying policy rule ID from `features/21_policy_engine` | Request role change or approval | Yes |
| `TOOL_NOT_ALLOWED` | 403 | AuthZ | Caller's role/policy does not permit invoking this tool | No | "This action isn't available for your role." | Tool ID + denying rule | Request elevated role | Yes |
| `FILE_CLASSIFICATION_DENIED` | 403 | AuthZ | Caller's clearance is below the file/document's classification level | No | "You don't have access to this document." | Document classification vs. caller clearance | Request access grant | Yes |
| `APPROVAL_REQUIRED` | 403 | AuthZ | Action is high-risk and awaiting approval; not yet denied, just blocked | No | "This action needs approval before it can run." | Approval record ID (pending) | Approver reviews `features/16_human_approval` request | Yes |
| `APPROVAL_REJECTED` | 403 | AuthZ | An approver explicitly rejected the pending action | No | "This action was not approved." | Approval record ID + rejection reason | Revise and resubmit, or escalate | Yes |
| `NETWORK_EGRESS_BLOCKED` | 403 | Sovereignty | Code/tool attempted an outbound connection not permitted by the active network mode | No | "This operation attempted a network connection that isn't allowed in this deployment." | Target host:port, active `NETWORK_MODE` | N/A — this is the system working correctly | Yes |
| `FILE_NOT_FOUND` | 404 | Resource | Referenced file/document/resource does not exist or is not visible to caller | No | "That item couldn't be found." | Resource ID | Verify ID / re-upload | No |
| `RESOURCE_CONFLICT` | 409 | State | Operation conflicts with the resource's current state (e.g. double-approve) | No | "This item was already updated by someone else." | Current state vs. expected state | Refresh and retry with current state | Yes |
| `MODEL_NOT_APPROVED` | 403 | Policy | Selected/requested model is not approved for the request's classification level | No | "This request requires a model that isn't approved for this data's classification." | Model ID, required classification, model's approved classification ceiling | Use an approved model or reclassify | Yes |
| `MODEL_UNAVAILABLE` | 503 | Dependency | Target model runtime is not currently loaded/reachable | Yes | "The AI model is temporarily unavailable — retrying." | Model ID, runtime health check result | Router falls back per `features/02_model_router/09_fallback_routing.md` | Yes |
| `MODEL_RESOURCE_EXHAUSTED` | 503 | Dependency | GPU/VRAM/CPU budget exceeded for requested model | Yes (after backoff) | "The system is at capacity — please try again shortly." | VRAM/CPU utilization at time of request | Wait, or router falls back to a smaller model | Yes |
| `INFERENCE_TIMEOUT` | 504 | Dependency | Inference call exceeded its timeout budget (see `runtime/12_timeout_policy.md`) | Yes | "The AI model took too long to respond." | Model ID, elapsed time, configured timeout | Retry once per retry policy, then surface to user | Yes |
| `TOOL_EXECUTION_FAILED` | 500 | Execution | Tool ran but returned a failure result | Depends on tool (see tool's own doc) | "One of the steps in this task failed." | Tool ID, tool's own error payload | Agent kernel replans or surfaces to user | Yes |
| `SANDBOX_LIMIT_EXCEEDED` | 500 | Execution | Code execution exceeded CPU/memory/time/output-size limit | No | "The code execution was stopped for exceeding resource limits." | Which limit, configured value, observed value | Reduce workload or request limit review | Yes |
| `RAG_INDEX_UNAVAILABLE` | 503 | Dependency | Vector or keyword index is unreachable | Yes | "Search is temporarily unavailable." | Which index (pgvector/tsvector), health check result | Retry per retry policy | Yes |
| `DEPENDENCY_UNAVAILABLE` | 503 | Dependency | Generic: a required internal service (DB, object storage, queue) is unreachable | Yes | "A required service is temporarily unavailable." | Service name, health check result | Retry per retry policy; operator paged if sustained | Yes |
| `RATE_LIMITED` | 429 | Throttling | Caller exceeded the per-user rate limit for this operation class (`schemas/02_api_schema.md`) | Yes (after `Retry-After` delay) | "You're doing that too quickly — please wait a moment." | Operation class, limit, current count | Wait for `Retry-After` header value | No (high volume; sampled logging instead, see `features/25_observability/`) |
| `INTERNAL_ERROR` | 500 | Internal | Unhandled/unexpected error | No (unless caller sets idempotency key and it's known-safe) | "Something went wrong on our end." | Stack trace / exception, correlation ID | File a bug; never silently retried without idempotency key | Yes — always |

## Rules for using this registry

1. Every failure surfaced to a caller (API response, tool result, agent-visible error) MUST use
   exactly one code from this table.
2. If a feature genuinely needs a code not listed here, it is added to this table — not
   invented locally — in the same pull request that introduces the need.
3. `Audit?` = Yes means: every occurrence of this error MUST produce an `AuditEvent`
   (`schemas/15_audit_event_schema.md`) with `result=error`, `error_code=<code>`.
4. Feature documents reference this table as: "On failure, returns one of:
   `CODE_A`, `CODE_B` (see `reference/01_error_codes.md`)" — they do not redefine status
   codes or messages inline.
