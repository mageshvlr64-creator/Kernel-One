# Policy Fit

> Feature group: **Model Router** (`docs/features/02_model_router/`) · File: `06_policy_fit.md`
> Part of the Sovereign AI Workbench (SIH26176) specification set. Risk level: **low**.
> Previous: `05_resource_fit.md` · Next: `07_accuracy_fit.md`

## 1. Purpose

**Policy Fit** is the unit of Model Router responsible for the router selecting which local model handles a task by capability, policy, and resource fit as it specifically relates to "policy fit." It exists as its own document because it has its own inputs, its own failure modes, and its own permission boundary — distinct from the other files in `docs/features/02_model_router/`.

## 2. Scope

In scope: validating and executing the `policy fit` operation, updating the `routing_decisions` store, and emitting the corresponding audit event (`model_router.policy_fit`). Out of scope: anything owned by a sibling file in this feature group, and anything listed under Non-goals below.

## 3. Non-goals

Policy Fit does not perform its own permission check logic — it calls the shared RBAC layer (`docs/features/19_identity_and_rbac/05_permissions.md`). It does not decide routing or model selection itself. It does not write directly to the audit table — it emits an event that `docs/features/17_audit/` consumes. It makes zero outbound network calls outside the active network mode.

## 4. User-facing behavior

From the workbench UI, policy fit is triggered by the corresponding action in the relevant panel (see `docs/ui/`) or issued programmatically via `POST /api/v1/model-router/policy-fit`. On success the UI reflects the new state within one refresh cycle (≤ 1s). On failure the UI shows a specific, human-readable message mapped from the error code table below — never a raw stack trace or a silent no-op.

## 5. System behavior

1) Request arrives at `/api/v1/model-router/policy-fit` and passes through auth + RBAC + policy checks. 2) The `Model Router` service validates the payload against its schema. 3) The operation is applied to the `routing_decisions` store inside a single transaction. 4) An audit event `model_router.policy_fit` is emitted. 5) The response is returned to the caller. Steps 3-4 are atomic: if step 4 cannot be guaranteed, step 3 is rolled back rather than leaving an unaudited state change.

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

On success: the `routing_decisions` row reflects the new state; exactly one audit event `model_router.policy_fit` exists for this invocation; any cache or index derived from `routing_decisions` is invalidated or updated in the same logical operation. On failure: no partial write is visible to any other caller.

## 10. Data structures

Canonical shape lives in `docs/schemas/` (see the schema file matching `routing_decisions`) and `docs/domain/` for the entity-level definition. This file does not redefine those fields — it only specifies which of them `Policy Fit` reads or writes.

## 11. API contracts

`POST /api/v1/model-router/policy-fit` — create/invoke. `GET /api/v1/model-router/policy-fit/{id}` — read current state. Full request/response schema, headers, and pagination (where applicable) are defined in `docs/api/` under the entry for `Model Router`. Auth: Bearer session token, required on every call, no anonymous access.

## 12. Internal interfaces

Backend module: `model_router_policy_fit_service`, exposing a single entry point `handle_policy_fit(context, payload) -> Result`. Callers (e.g. the agent kernel's tool selection step, or the admin console) invoke this function directly for in-process calls; the HTTP route above is a thin wrapper around the same function — there is exactly one implementation, not two.

## 13. State transitions

Policy Fit moves its resource through the states defined in the relevant `docs/runtime/` state machine file for `Model Router`. It is only permitted to trigger the specific transition(s) relevant to "policy fit" — any other transition is a defect, and the state machine layer must reject it rather than silently allow it.

## 14. Dependencies

Hard dependencies: `docs/features/01_model_management/`, `docs/features/03_inference_gateway/`, `docs/features/21_policy_engine/`. If any hard dependency is unavailable, Policy Fit fails closed per Failure modes — it does not silently degrade to an unsafe default.

**Traceability:** this feature implements `REQ-AI-001`, `REQ-AI-003` (see `docs/03_REQUIREMENTS.md`).


## 15. Security requirements

All input is treated as untrusted and validated against its schema before use. No input is interpolated into a shell command, SQL string, or filesystem path without going through the sanitization described in `docs/security/09_path_traversal.md` and `docs/security/17_malicious_documents.md` where relevant. If policy fit processes agent- or model-generated content, it is treated as untrusted per `docs/security/05_prompt_injection.md`.

## 16. Permission requirements

Resource: `Model` · Action: `execute` · Risk level: **low**.

Role access for this resource/action pair is defined once, canonically, in `docs/reference/05_permission_matrix.md` — this file does not repeat that table. In addition to the base role check, the policy engine (`docs/features/21_policy_engine/`) evaluates the classification and workspace conditions documented in that same file.

A denied call returns `POLICY_DENIED` or `TOOL_NOT_ALLOWED` (see `docs/reference/01_error_codes.md`) and is logged to `docs/features/17_audit/` with the caller's role and the specific denying rule — never a silent no-op.

## 17. Failure modes

This feature returns errors exclusively from the canonical registry in `docs/reference/01_error_codes.md`. The codes most relevant to this feature:

| Error code (see registry for HTTP status, message, remediation) |
|---|
| `MODEL_UNAVAILABLE` |
| `MODEL_NOT_APPROVED` |
| `MODEL_RESOURCE_EXHAUSTED` |
| `INTERNAL_ERROR` (always possible; see registry) |

No other error code may be returned by this feature without first being added to the registry. Each occurrence is a required audit event per `docs/schemas/15_audit_event_schema.md`.

## 18. Retry behavior

This feature's calls are classified **`interactive-read`** operations. Exact timeout, retry count, backoff, and circuit-breaker thresholds for this class are defined once, canonically, in `docs/runtime/11_retry_policy.md` — this file does not restate those numbers. If this feature's actual behavior needs a different class than `interactive-read`, that is a discrepancy to resolve in the canonical policy file, not a reason to define a local exception here.

## 19. Timeout behavior

See the **`interactive-read`** row in `docs/runtime/11_retry_policy.md` for the exact timeout value and its provenance label (CONFIG DEFAULT / DESIGN LIMIT / BENCHMARKED). On timeout, this feature returns the timeout-class error code from `docs/reference/01_error_codes.md` (typically `INFERENCE_TIMEOUT` for model calls or `DEPENDENCY_UNAVAILABLE`/`SANDBOX_LIMIT_EXCEEDED` for tool/infra calls — see Failure modes above for this feature's specific set) and releases any resource it holds (subprocess, container, DB transaction, lock).

## 20. Recovery behavior

On failure, no partial state from Policy Fit is left visible. If Policy Fit is a step inside an agent plan, the agent kernel's replanning logic (`docs/features/04_agent_kernel/10_replanning.md`) decides whether to retry, substitute a different approach, or surface the failure to the user, per `docs/runtime/14_resume_and_recovery.md`.

## 21. Observability requirements

Emits one structured log line per invocation (`level`, `event=model_router.policy_fit`, `actor_id`, `duration_ms`, `outcome`) and one metric `model_router_policy_fit_duration_seconds` (histogram) plus `model_router_policy_fit_total{outcome}` (counter), per `docs/features/25_observability/03_metrics.md`.

## 22. Audit requirements

Every invocation, successful or not, produces exactly one `AuditEvent` of type `model_router.policy_fit` conforming to the canonical schema in `docs/schemas/15_audit_event_schema.md` — this file does not redefine the `AuditEvent` field set. `resource_type` is `Model`; `action` is `execute`; `classification` is populated when the resource carries one (`docs/features/20_data_classification/`).

## 23. Performance requirements

p95 < 50ms for a routing decision, excluding the downstream inference call itself. Measured and enforced per `docs/performance/01_performance_requirements.md` on the reference hardware profile in `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`. **Status: DESIGN LIMIT** — this budget is an engineering target chosen for demo usability on the reference hardware profile, not yet a benchmark-verified measurement (see `docs/20_DECISION_LOG.md` DEC-014 for the pending validation step). Treat it as a target to test against, not a guaranteed SLA, until DEC-014 is resolved.

## 24. Test requirements

Minimum coverage: one unit test per row in the Failure modes table above, one integration test for the full success path through `/api/v1/model-router/policy-fit`, and one permission test per role in the table above (three roles × allow/deny = at least 3 assertions), per `docs/testing/01_testing_strategy.md`.

## 25. Acceptance criteria

- [ ] `POST /api/v1/model-router/policy-fit` succeeds for an `admin` caller with a valid payload and returns the shape in Outputs.
- [ ] The same call is denied per the Permission requirements table for a disallowed role, with the correct error code.
- [ ] Exactly one `model_router.policy_fit` audit event is produced per invocation, success or failure.
- [ ] The operation completes within the budget stated in Performance requirements on reference hardware.
- [ ] No outbound network call occurs during execution.

## 26. Definition of done

Policy Fit is done when all Acceptance criteria above pass in CI, the corresponding `docs/schemas/` and `docs/api/` entries match the implementation exactly, and the checklist in `docs/11_DEFINITION_OF_DONE.md` is satisfied.

## 27. Implementation notes

Implement `model_router.policy_fit` as a single service function called by both the HTTP route and any internal caller (e.g. the agent kernel) — do not duplicate the logic. Reuse the shared RBAC/policy check helper rather than writing a new role comparison; reuse the shared audit-emit helper rather than writing to the audit table directly.

## 28. Forbidden implementations

Do not check `role` via a client-supplied field. Do not perform the `routing_decisions` write and the audit write as two separate, independently-failable operations. Do not add a bypass flag (e.g. `skip_approval=true`) reachable from the API. Do not call any host outside `localhost`/internal service addresses from within this operation.

## 29. Examples

**Success:** `admin` calls `POST /api/v1/model-router/policy-fit` with a valid payload → `200 OK`, `{"status": "ok", "resource_id": "…", "state": "the resulting state (see `docs/runtime/_state_machines_canonical.md`)"}`, one `model_router.policy_fit` audit event recorded.

**Denied:** `restricted` calls the same endpoint → `403`, `MR-4030`, audit event recorded with `outcome=denied`.

## 30. Edge cases

Empty/missing `payload` → `400` before any state is touched. Duplicate call with the same `idempotency_key` within the retry window → returns the original result, does not re-execute. Concurrent calls targeting the same `resource_id` → the later call observes the row-level lock and either waits or receives `409`, never a silent lost update. Dependency listed above is degraded but not fully down → Policy Fit fails closed rather than guessing.
