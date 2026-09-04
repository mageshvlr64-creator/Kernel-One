# Tool Access

> Feature group: **Identity and RBAC** (`docs/features/19_identity_and_rbac/`) · File: `10_tool_access.md`
> Part of the Sovereign AI Workbench (SIH26176) specification set. Risk level: **high**.
> Previous: `09_document_access.md` · Next: `11_model_access.md`

## 1. Purpose

**Tool Access** is the unit of Identity and RBAC responsible for identity and role-based access control governing who can do what as it specifically relates to "tool access." It exists as its own document because it has its own inputs, its own failure modes, and its own permission boundary — distinct from the other files in `docs/features/19_identity_and_rbac/`.

## 2. Scope

In scope: validating and executing the `tool access` operation, updating the `users / roles / permissions` store, and emitting the corresponding audit event (`identity_and_rbac.tool_access`). Out of scope: anything owned by a sibling file in this feature group, and anything listed under Non-goals below.

## 3. Non-goals

Tool Access does not perform its own permission check logic — it calls the shared RBAC layer (`docs/features/19_identity_and_rbac/05_permissions.md`). It does not decide routing or model selection itself. It does not write directly to the audit table — it emits an event that `docs/features/17_audit/` consumes. It makes zero outbound network calls outside the active network mode.

## 4. User-facing behavior

From the workbench UI, tool access is triggered by the corresponding action in the relevant panel (see `docs/ui/`) or issued programmatically via `POST /api/v1/identity-and-rbac/tool-access`. On success the UI reflects the new state within one refresh cycle (≤ 1s). On failure the UI shows a specific, human-readable message mapped from the error code table below — never a raw stack trace or a silent no-op.

## 5. System behavior

1) Request arrives at `/api/v1/identity-and-rbac/tool-access` and passes through auth + RBAC + policy checks. 2) The `Identity and RBAC` service validates the payload against its schema. 3) The operation is applied to the `users / roles / permissions` store inside a single transaction. 4) An audit event `identity_and_rbac.tool_access` is emitted. 5) The response is returned to the caller. Steps 3-4 are atomic: if step 4 cannot be guaranteed, step 3 is rolled back rather than leaving an unaudited state change.

## 6. Inputs

```json
{
  "actor_id": "string (uuid, required)",
  "workspace_id": "string (uuid, required)",
  "resource_id": "string (uuid, optional — omitted on create)",
  "payload": "object (required; request envelope defined in `docs/schemas/02_api_schema.md`, entity-specific fields defined in the `docs/schemas/` file matching this feature group)",
  "idempotency_key": "string (optional, recommended for retryable calls)"
}
```
`actor_id` and `workspace_id` are populated from the authenticated session, never trusted from client-supplied body fields.

## 7. Outputs

```json
{
  "status": "ok | error",
  "resource_id": "string (uuid)",
  "state": "string — one of the states enumerated for this resource in `docs/runtime/_state_machines_canonical.md`",
  "audit_event_id": "string (uuid)",
  "timestamp": "ISO-8601 string"
}
```

## 8. Preconditions

Caller is authenticated (`docs/features/19_identity_and_rbac/02_authentication.md`). Caller's role passes the permission table below. Referenced `resource_id` (if any) exists and is visible to the caller's workspace/classification scope (`docs/features/20_data_classification/`). Any upstream dependency listed below is healthy, or the operation fails closed per Failure modes.

## 9. Postconditions

On success: the `users / roles / permissions` row reflects the new state; exactly one audit event `identity_and_rbac.tool_access` exists for this invocation; any cache or index derived from `users / roles / permissions` is invalidated or updated in the same logical operation. On failure: no partial write is visible to any other caller.

## 10. Data structures

Canonical shape lives in `docs/schemas/` (see the schema file matching `users / roles / permissions`) and `docs/domain/` for the entity-level definition. This file does not redefine those fields — it only specifies which of them `Tool Access` reads or writes.

## 11. API contracts

`POST /api/v1/identity-and-rbac/tool-access` — create/invoke. `GET /api/v1/identity-and-rbac/tool-access/{id}` — read current state. Full request/response schema, headers, and pagination (where applicable) are defined in `docs/api/` under the entry for `Identity and RBAC`. Auth: Bearer session token, required on every call, no anonymous access.

## 12. Internal interfaces

Backend module: `identity_and_rbac_tool_access_service`, exposing a single entry point `handle_tool_access(context, payload) -> Result`. Callers (e.g. the agent kernel's tool selection step, or the admin console) invoke this function directly for in-process calls; the HTTP route above is a thin wrapper around the same function — there is exactly one implementation, not two.

## 13. State transitions

Tool Access moves its resource through the states defined in the relevant `docs/runtime/` state machine file for `Identity and RBAC`. It is only permitted to trigger the specific transition(s) relevant to "tool access" — any other transition is a defect, and the state machine layer must reject it rather than silently allow it.

## 14. Dependencies

Hard dependencies: `docs/features/21_policy_engine/`, `docs/features/17_audit/`. If any hard dependency is unavailable, Tool Access fails closed per Failure modes — it does not silently degrade to an unsafe default.

**Traceability:** this feature implements `REQ-SEC-001` (see `docs/03_REQUIREMENTS.md`).


## 15. Security requirements

All input is treated as untrusted and validated against its schema before use. No input is interpolated into a shell command, SQL string, or filesystem path without going through the sanitization described in `docs/security/09_path_traversal.md` and `docs/security/17_malicious_documents.md` where relevant. If tool access processes agent- or model-generated content, it is treated as untrusted per `docs/security/05_prompt_injection.md`.

## 16. Permission requirements

Resource: `User` · Action: `execute` · Risk level: **high**.

Role access for this resource/action pair is defined once, canonically, in `docs/reference/05_permission_matrix.md` — this file does not repeat that table. In addition to the base role check, the policy engine (`docs/features/21_policy_engine/`) evaluates the classification and workspace conditions documented in that same file, and — because this action is risk=high — the approval condition (an `Approval` record with `decision=approved` must exist before this action executes, per `docs/features/16_human_approval/`).

A denied call returns `POLICY_DENIED` or `TOOL_NOT_ALLOWED` (see `docs/reference/01_error_codes.md`) and is logged to `docs/features/17_audit/` with the caller's role and the specific denying rule — never a silent no-op.

## 17. Failure modes

This feature returns errors exclusively from the canonical registry in `docs/reference/01_error_codes.md`. The codes most relevant to this feature:

| Error code (see registry for HTTP status, message, remediation) |
|---|
| `AUTH_REQUIRED` |
| `POLICY_DENIED` |
| `INTERNAL_ERROR` (always possible; see registry) |

No other error code may be returned by this feature without first being added to the registry. Each occurrence is a required audit event per `docs/schemas/15_audit_event_schema.md`.

## 18. Retry behavior

This feature's calls are classified **`interactive-read`** operations. Exact timeout, retry count, backoff, and circuit-breaker thresholds for this class are defined once, canonically, in `docs/runtime/11_retry_policy.md` — this file does not restate those numbers. If this feature's actual behavior needs a different class than `interactive-read`, that is a discrepancy to resolve in the canonical policy file, not a reason to define a local exception here.

## 19. Timeout behavior

See the **`interactive-read`** row in `docs/runtime/11_retry_policy.md` for the exact timeout value and its provenance label (CONFIG DEFAULT / DESIGN LIMIT / BENCHMARKED). On timeout, this feature returns the timeout-class error code from `docs/reference/01_error_codes.md` (typically `INFERENCE_TIMEOUT` for model calls or `DEPENDENCY_UNAVAILABLE`/`SANDBOX_LIMIT_EXCEEDED` for tool/infra calls — see Failure modes above for this feature's specific set) and releases any resource it holds (subprocess, container, DB transaction, lock).

## 20. Recovery behavior

On failure, no partial state from Tool Access is left visible. If Tool Access is a step inside an agent plan, the agent kernel's replanning logic (`docs/features/04_agent_kernel/10_replanning.md`) decides whether to retry, substitute a different approach, or surface the failure to the user, per `docs/runtime/14_resume_and_recovery.md`.

## 21. Observability requirements

Emits one structured log line per invocation (`level`, `event=identity_and_rbac.tool_access`, `actor_id`, `duration_ms`, `outcome`) and one metric `identity_and_rbac_tool_access_duration_seconds` (histogram) plus `identity_and_rbac_tool_access_total{outcome}` (counter), per `docs/features/25_observability/03_metrics.md`.

## 22. Audit requirements

Every invocation, successful or not, produces exactly one `AuditEvent` of type `identity_and_rbac.tool_access` conforming to the canonical schema in `docs/schemas/15_audit_event_schema.md` — this file does not redefine the `AuditEvent` field set. `resource_type` is `User`; `action` is `execute`; `classification` is populated when the resource carries one (`docs/features/20_data_classification/`).

## 23. Performance requirements

permission check p95 < 5ms (in-memory lookup). Measured and enforced per `docs/performance/01_performance_requirements.md` on the reference hardware profile in `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`. **Status: DESIGN LIMIT** — this budget is an engineering target chosen for demo usability on the reference hardware profile, not yet a benchmark-verified measurement (see `docs/20_DECISION_LOG.md` DEC-014 for the pending validation step). Treat it as a target to test against, not a guaranteed SLA, until DEC-014 is resolved.

## 24. Test requirements

Minimum coverage: one unit test per row in the Failure modes table above, one integration test for the full success path through `/api/v1/identity-and-rbac/tool-access`, and one permission test per role in the table above (three roles × allow/deny = at least 3 assertions), per `docs/testing/01_testing_strategy.md`.

## 25. Acceptance criteria

- [ ] `POST /api/v1/identity-and-rbac/tool-access` succeeds for an `admin` caller with a valid payload and returns the shape in Outputs.
- [ ] The same call is denied per the Permission requirements table for a disallowed role, with the correct error code.
- [ ] Exactly one `identity_and_rbac.tool_access` audit event is produced per invocation, success or failure.
- [ ] The operation completes within the budget stated in Performance requirements on reference hardware.
- [ ] No outbound network call occurs during execution.

## 26. Definition of done

Tool Access is done when all Acceptance criteria above pass in CI, the corresponding `docs/schemas/` and `docs/api/` entries match the implementation exactly, and the checklist in `docs/11_DEFINITION_OF_DONE.md` is satisfied.

## 27. Implementation notes

Implement `identity_and_rbac.tool_access` as a single service function called by both the HTTP route and any internal caller (e.g. the agent kernel) — do not duplicate the logic. Reuse the shared RBAC/policy check helper rather than writing a new role comparison; reuse the shared audit-emit helper rather than writing to the audit table directly.

## 28. Forbidden implementations

Do not check `role` via a client-supplied field. Do not perform the `users / roles / permissions` write and the audit write as two separate, independently-failable operations. Do not add a bypass flag (e.g. `skip_approval=true`) reachable from the API. Do not call any host outside `localhost`/internal service addresses from within this operation.

## 29. Examples

**Success:** `admin` calls `POST /api/v1/identity-and-rbac/tool-access` with a valid payload → `200 OK`, `{"status": "ok", "resource_id": "…", "state": "the resulting state (see `docs/runtime/_state_machines_canonical.md`)"}`, one `identity_and_rbac.tool_access` audit event recorded.

**Denied:** `restricted` calls the same endpoint → `403`, `IAR-4030`, audit event recorded with `outcome=denied`.

## 30. Edge cases

Empty/missing `payload` → `400` before any state is touched. Duplicate call with the same `idempotency_key` within the retry window → returns the original result, does not re-execute. Concurrent calls targeting the same `resource_id` → the later call observes the row-level lock and either waits or receives `409`, never a silent lost update. Dependency listed above is degraded but not fully down → Tool Access fails closed rather than guessing.
