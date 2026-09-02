# Read Permissions

> Feature group: **Filesystem Tool** (`docs/features/06_filesystem_tool/`) · File: `02_read_permissions.md`
> Part of the Sovereign AI Workbench (SIH26176) specification set. Risk level: **medium**.
> Previous: `01_filesystem_tool.md` · Next: `03_write_permissions.md`

## 1. Purpose

**Read Permissions** is the unit of Filesystem Tool responsible for sandboxed, workspace-scoped file access for agents as it specifically relates to "read permissions." It exists as its own document because it has its own inputs, its own failure modes, and its own permission boundary — distinct from the other files in `docs/features/06_filesystem_tool/`.

## 2. Scope

In scope: validating and executing the `read permissions` operation, updating the `filesystem_operations` store, and emitting the corresponding audit event (`filesystem_tool.read_permissions`). Out of scope: anything owned by a sibling file in this feature group, and anything listed under Non-goals below.

## 3. Non-goals

Read Permissions does not perform its own permission check logic — it calls the shared RBAC layer (`docs/features/19_identity_and_rbac/05_permissions.md`). It does not decide routing or model selection itself. It does not write directly to the audit table — it emits an event that `docs/features/17_audit/` consumes. It makes zero outbound network calls outside the active network mode.

## 4. User-facing behavior

From the workbench UI, read permissions is triggered by the corresponding action in the relevant panel (see `docs/ui/`) or issued programmatically via `POST /api/v1/filesystem-tool/read-permissions`. On success the UI reflects the new state within one refresh cycle (≤ 1s). On failure the UI shows a specific, human-readable message mapped from the error code table below — never a raw stack trace or a silent no-op.

## 5. System behavior

1) Request arrives at `/api/v1/filesystem-tool/read-permissions` and passes through auth + RBAC + policy checks. 2) The `Filesystem Tool` service validates the payload against its schema. 3) The operation is applied to the `filesystem_operations` store inside a single transaction. 4) An audit event `filesystem_tool.read_permissions` is emitted. 5) The response is returned to the caller. Steps 3-4 are atomic: if step 4 cannot be guaranteed, step 3 is rolled back rather than leaving an unaudited state change.

## 6. Inputs

```json
{
  "actor_id": "string (uuid, required)",
  "workspace_id": "string (uuid, required)",
  "resource_id": "string (uuid, optional — omitted on create)",
  "payload": "object (required, shape defined in docs/schemas/ for this resource)",
  "idempotency_key": "string (optional, recommended for retryable calls)"
}
```
`actor_id` and `workspace_id` are populated from the authenticated session, never trusted from client-supplied body fields.

## 7. Outputs

```json
{
  "status": "ok | error",
  "resource_id": "string (uuid)",
  "state": "string (see State transitions below)",
  "audit_event_id": "string (uuid)",
  "timestamp": "ISO-8601 string"
}
```

## 8. Preconditions

Caller is authenticated (`docs/features/19_identity_and_rbac/02_authentication.md`). Caller's role passes the permission table below. Referenced `resource_id` (if any) exists and is visible to the caller's workspace/classification scope (`docs/features/20_data_classification/`). Any upstream dependency listed below is healthy, or the operation fails closed per Failure modes.

## 9. Postconditions

On success: the `filesystem_operations` row reflects the new state; exactly one audit event `filesystem_tool.read_permissions` exists for this invocation; any cache or index derived from `filesystem_operations` is invalidated or updated in the same logical operation. On failure: no partial write is visible to any other caller.

## 10. Data structures

Canonical shape lives in `docs/schemas/` (see the schema file matching `filesystem_operations`) and `docs/domain/` for the entity-level definition. This file does not redefine those fields — it only specifies which of them `Read Permissions` reads or writes.

## 11. API contracts

`POST /api/v1/filesystem-tool/read-permissions` — create/invoke. `GET /api/v1/filesystem-tool/read-permissions/{id}` — read current state. Full request/response schema, headers, and pagination (where applicable) are defined in `docs/api/` under the entry for `Filesystem Tool`. Auth: Bearer session token, required on every call, no anonymous access.

## 12. Internal interfaces

Backend module: `filesystem_tool_read_permissions_service`, exposing a single entry point `handle_read_permissions(context, payload) -> Result`. Callers (e.g. the agent kernel's tool selection step, or the admin console) invoke this function directly for in-process calls; the HTTP route above is a thin wrapper around the same function — there is exactly one implementation, not two.

## 13. State transitions

Read Permissions moves its resource through the states defined in the relevant `docs/runtime/` state machine file for `Filesystem Tool`. It is only permitted to trigger the specific transition(s) relevant to "read permissions" — any other transition is a defect, and the state machine layer must reject it rather than silently allow it.

## 14. Dependencies

Hard dependencies: `docs/features/05_tool_gateway/`, `docs/features/09_code_execution/`. If any hard dependency is unavailable, Read Permissions fails closed per Failure modes — it does not silently degrade to an unsafe default.

## 15. Security requirements

All input is treated as untrusted and validated against its schema before use. No input is interpolated into a shell command, SQL string, or filesystem path without going through the sanitization described in `docs/security/09_path_traversal.md` and `docs/security/17_malicious_documents.md` where relevant. If read permissions processes agent- or model-generated content, it is treated as untrusted per `docs/security/05_prompt_injection.md`.

## 16. Permission requirements

Risk level: **medium**.

| Role | Access |
|---|---|
| `admin` | allow |
| `operator` | allow |
| `restricted` | deny |

A denied call returns HTTP 403 with error code `FT-4030` and is logged to `docs/features/17_audit/` with the caller's role and the missing permission — never a silent no-op.

## 17. Failure modes

| Code | HTTP status | Meaning |
|---|---|---|
| `FT-4001` | 400 | Request failed schema validation |
| `FT-4030` | 403 | Caller's role/permission does not allow this operation |
| `FT-4040` | 404 | Referenced resource does not exist or caller cannot see it |
| `FT-4090` | 409 | Operation conflicts with current resource state |
| `FT-5040` | 504 | Downstream dependency exceeded its timeout budget |
| `FT-5030` | 503 | Required dependency is down or degraded |
| `FT-5000` | 500 | Unexpected internal error; always paired with an audit event |

Each row above maps to a named entry in `docs/failures/` for this subsystem; no failure produced by Read Permissions is allowed to exist without a corresponding documented failure mode.

## 18. Retry behavior

Read Permissions is treated as retryable: up to 3 attempt(s) with exponential backoff starting at 400ms, per `docs/runtime/11_retry_policy.md`. Retries are only issued for `503`/`504`-class failures, never for `400`/`403`/`409`.

## 19. Timeout behavior

Maximum execution time: **53s**, enforced per `docs/runtime/12_timeout_policy.md`. On timeout, any in-flight subprocess, container, or DB transaction opened by Read Permissions is terminated/rolled back and the caller receives the `504` error from the table above.

## 20. Recovery behavior

On failure, no partial state from Read Permissions is left visible. If Read Permissions is a step inside an agent plan, the agent kernel's replanning logic (`docs/features/04_agent_kernel/10_replanning.md`) decides whether to retry, substitute a different approach, or surface the failure to the user, per `docs/runtime/14_resume_and_recovery.md`.

## 21. Observability requirements

Emits one structured log line per invocation (`level`, `event=filesystem_tool.read_permissions`, `actor_id`, `duration_ms`, `outcome`) and one metric `filesystem_tool_read_permissions_duration_seconds` (histogram) plus `filesystem_tool_read_permissions_total{outcome}` (counter), per `docs/features/25_observability/03_metrics.md`.

## 22. Audit requirements

Every invocation, successful or not, produces one audit event of type `filesystem_tool.read_permissions` containing `actor_id`, `workspace_id`, `resource_id`, a hash of the payload (never the raw payload if it may contain sensitive content), and `outcome`, per `docs/features/17_audit/03_event_schema.md`.

## 23. Performance requirements

p95 < 50ms per read/write under 1MB. Measured and enforced per `docs/performance/01_performance_requirements.md` on the reference hardware profile in `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`.

## 24. Test requirements

Minimum coverage: one unit test per row in the Failure modes table above, one integration test for the full success path through `/api/v1/filesystem-tool/read-permissions`, and one permission test per role in the table above (three roles × allow/deny = at least 3 assertions), per `docs/testing/01_testing_strategy.md`.

## 25. Acceptance criteria

- [ ] `POST /api/v1/filesystem-tool/read-permissions` succeeds for an `admin` caller with a valid payload and returns the shape in Outputs.
- [ ] The same call is denied per the Permission requirements table for a disallowed role, with the correct error code.
- [ ] Exactly one `filesystem_tool.read_permissions` audit event is produced per invocation, success or failure.
- [ ] The operation completes within the budget stated in Performance requirements on reference hardware.
- [ ] No outbound network call occurs during execution.

## 26. Definition of done

Read Permissions is done when all Acceptance criteria above pass in CI, the corresponding `docs/schemas/` and `docs/api/` entries match the implementation exactly, and the checklist in `docs/11_DEFINITION_OF_DONE.md` is satisfied.

## 27. Implementation notes

Implement `filesystem_tool.read_permissions` as a single service function called by both the HTTP route and any internal caller (e.g. the agent kernel) — do not duplicate the logic. Reuse the shared RBAC/policy check helper rather than writing a new role comparison; reuse the shared audit-emit helper rather than writing to the audit table directly.

## 28. Forbidden implementations

Do not check `role` via a client-supplied field. Do not perform the `filesystem_operations` write and the audit write as two separate, independently-failable operations. Do not add a bypass flag (e.g. `skip_approval=true`) reachable from the API. Do not call any host outside `localhost`/internal service addresses from within this operation.

## 29. Examples

**Success:** `admin` calls `POST /api/v1/filesystem-tool/read-permissions` with a valid payload → `200 OK`, `{"status": "ok", "resource_id": "…", "state": "<next-state>"}`, one `filesystem_tool.read_permissions` audit event recorded.

**Denied:** `restricted` calls the same endpoint → `403`, `FT-4030`, audit event recorded with `outcome=denied`.

## 30. Edge cases

Empty/missing `payload` → `400` before any state is touched. Duplicate call with the same `idempotency_key` within the retry window → returns the original result, does not re-execute. Concurrent calls targeting the same `resource_id` → the later call observes the row-level lock and either waits or receives `409`, never a silent lost update. Dependency listed above is degraded but not fully down → Read Permissions fails closed rather than guessing.
