# Confidence

> Feature group: **Evidence and Provenance** (`docs/features/14_evidence_and_provenance/`) · File: `08_confidence.md`
> Part of the Sovereign AI Workbench (SIH26117) specification set. Risk level: **low**.
> Previous: `07_evidence_graph.md` · Next: `09_unsupported_claim_detection.md`

## 1. Purpose

**Confidence** computes and exposes how much a user should trust a piece of Evidence, without
presenting a bare number as a correctness probability. Per
`SIH26117_Documentation_Refactor_Master_Prompt.txt` §12, "Confidence = 94%" with no calibration
methodology is an explicit anti-pattern this feature is designed to avoid. It reads the fields
defined in `docs/domain/13_evidence_model.md` (`confidence`, `source_authority`,
`verification_status`) and `docs/domain/06_document_model.md` (`effective_from`,
`effective_until`) and derives the four-part qualitative representation the UI actually shows.

## 2. Scope

In scope: computing the qualitative Evidence Coverage / Source Authority / Freshness /
Cross-Source Agreement representation for a given answer's set of Evidence rows, and exposing
the raw retrieval `confidence` score separately, clearly labeled, for an operator debug view.
Out of scope: performing retrieval or reranking itself (owned by
`docs/features/13_knowledge_fabric/`), and detecting contradictions between sources (owned by
`docs/industrial/14_knowledge_conflict_detection.md`, which writes the `verification_status`
field this feature reads).

## 3. Non-goals

Confidence does not compute the retrieval/rerank score itself — that number is produced
during retrieval (`docs/features/13_knowledge_fabric/10_reranking.md`) and stored on the
Evidence row already. Confidence does not decide whether two sources conflict — that's
`industrial/14_knowledge_conflict_detection.md`'s job; this feature only reads its output
(`verification_status = contradicted`). It does not perform its own permission check logic —
it calls the shared RBAC layer (`docs/features/19_identity_and_rbac/05_permissions.md`). It
makes zero outbound network calls outside the active network mode.

## 3a. Methodology (the part this file previously omitted)

For a given answer, each cited Evidence row is scored on four qualitative axes, each derived
from an already-stored field rather than invented at display time:

| Axis | Derived from | Displayed values |
|---|---|---|
| Evidence coverage | Ratio of claims in the answer with ≥1 matching Evidence row, to total claims | High / Partial / Low |
| Source authority | `Evidence.source_authority` (denormalized from `Document.authority`) | Primary / Secondary / Reference |
| Freshness | `Document.effective_from`/`effective_until` vs. current date (or the query's target date, if the query was date-scoped) | Current / Superseded / Undated |
| Cross-source agreement | `Evidence.verification_status` | Agreement / Contradicted / Unverified |

No single 0–100% number is computed by combining these four axes — the master prompt's §12
explicitly warns against fake precision from combining heterogeneous signals into one score.
The four axes are shown as four separate, independently-understandable pieces of information;
a user (or judge) can see *why* something is trustworthy or isn't, rather than trusting an
opaque percentage. The raw `confidence` retrieval score remains available in a clearly-labeled
debug view for operators, described as a ranking signal, not a correctness estimate.

## 4. User-facing behavior

From the workbench UI, confidence is triggered by the corresponding action in the relevant panel (see `docs/ui/`) or issued programmatically via `POST /api/v1/evidence-and-provenance/confidence`. On success the UI reflects the new state within one refresh cycle (≤ 1s). On failure the UI shows a specific, human-readable message mapped from the error code table below — never a raw stack trace or a silent no-op.

## 5. System behavior

1) Request arrives at `/api/v1/evidence-and-provenance/confidence` and passes through auth + RBAC + policy checks. 2) The `Evidence and Provenance` service validates the payload against its schema. 3) The operation is applied to the `evidence_links` store inside a single transaction. 4) An audit event `evidence_and_provenance.confidence` is emitted. 5) The response is returned to the caller. Steps 3-4 are atomic: if step 4 cannot be guaranteed, step 3 is rolled back rather than leaving an unaudited state change.

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

On success: the `evidence_links` row reflects the new state; exactly one audit event `evidence_and_provenance.confidence` exists for this invocation; any cache or index derived from `evidence_links` is invalidated or updated in the same logical operation. On failure: no partial write is visible to any other caller.

## 10. Data structures

Canonical shape lives in `docs/schemas/` (see the schema file matching `evidence_links`) and `docs/domain/` for the entity-level definition. This file does not redefine those fields — it only specifies which of them `Confidence` reads or writes.

## 11. API contracts

`POST /api/v1/evidence-and-provenance/confidence` — create/invoke. `GET /api/v1/evidence-and-provenance/confidence/{id}` — read current state. Full request/response schema, headers, and pagination (where applicable) are defined in `docs/api/` under the entry for `Evidence and Provenance`. Auth: Bearer session token, required on every call, no anonymous access.

## 12. Internal interfaces

Backend module: `evidence_and_provenance_confidence_service`, exposing a single entry point `handle_confidence(context, payload) -> Result`. Callers (e.g. the agent kernel's tool selection step, or the admin console) invoke this function directly for in-process calls; the HTTP route above is a thin wrapper around the same function — there is exactly one implementation, not two.

## 13. State transitions

Confidence moves its resource through the states defined in the relevant `docs/runtime/` state machine file for `Evidence and Provenance`. It is only permitted to trigger the specific transition(s) relevant to "confidence" — any other transition is a defect, and the state machine layer must reject it rather than silently allow it.

## 14. Dependencies

Hard dependencies: `docs/features/13_knowledge_fabric/`, `docs/features/04_agent_kernel/`. If any hard dependency is unavailable, Confidence fails closed per Failure modes — it does not silently degrade to an unsafe default.

**Traceability:** this feature implements `REQ-FUNC-005` (see `docs/03_REQUIREMENTS.md`).


## 15. Security requirements

All input is treated as untrusted and validated against its schema before use. No input is interpolated into a shell command, SQL string, or filesystem path without going through the sanitization described in `docs/security/09_path_traversal.md` and `docs/security/17_malicious_documents.md` where relevant. If confidence processes agent- or model-generated content, it is treated as untrusted per `docs/security/05_prompt_injection.md`.

## 16. Permission requirements

Resource: `Document` · Action: `execute` · Risk level: **low**.

Role access for this resource/action pair is defined once, canonically, in `docs/reference/05_permission_matrix.md` — this file does not repeat that table. In addition to the base role check, the policy engine (`docs/features/21_policy_engine/`) evaluates the classification and workspace conditions documented in that same file.

A denied call returns `POLICY_DENIED` or `TOOL_NOT_ALLOWED` (see `docs/reference/01_error_codes.md`) and is logged to `docs/features/17_audit/` with the caller's role and the specific denying rule — never a silent no-op.

## 17. Failure modes

This feature returns errors exclusively from the canonical registry in `docs/reference/01_error_codes.md`. The codes most relevant to this feature:

| Error code (see registry for HTTP status, message, remediation) |
|---|
| `FILE_NOT_FOUND` |
| `RAG_INDEX_UNAVAILABLE` |
| `INTERNAL_ERROR` (always possible; see registry) |

No other error code may be returned by this feature without first being added to the registry. Each occurrence is a required audit event per `docs/schemas/15_audit_event_schema.md`.

## 18. Retry behavior

This feature's calls are classified **`interactive-read`** operations. Exact timeout, retry count, backoff, and circuit-breaker thresholds for this class are defined once, canonically, in `docs/runtime/11_retry_policy.md` — this file does not restate those numbers. If this feature's actual behavior needs a different class than `interactive-read`, that is a discrepancy to resolve in the canonical policy file, not a reason to define a local exception here.

## 19. Timeout behavior

See the **`interactive-read`** row in `docs/runtime/11_retry_policy.md` for the exact timeout value and its provenance label (CONFIG DEFAULT / DESIGN LIMIT / BENCHMARKED). On timeout, this feature returns the timeout-class error code from `docs/reference/01_error_codes.md` (typically `INFERENCE_TIMEOUT` for model calls or `DEPENDENCY_UNAVAILABLE`/`SANDBOX_LIMIT_EXCEEDED` for tool/infra calls — see Failure modes above for this feature's specific set) and releases any resource it holds (subprocess, container, DB transaction, lock).

## 20. Recovery behavior

On failure, no partial state from Confidence is left visible. If Confidence is a step inside an agent plan, the agent kernel's replanning logic (`docs/features/04_agent_kernel/10_replanning.md`) decides whether to retry, substitute a different approach, or surface the failure to the user, per `docs/runtime/14_resume_and_recovery.md`.

## 21. Observability requirements

Emits one structured log line per invocation (`level`, `event=evidence_and_provenance.confidence`, `actor_id`, `duration_ms`, `outcome`) and one metric `evidence_and_provenance_confidence_duration_seconds` (histogram) plus `evidence_and_provenance_confidence_total{outcome}` (counter), per `docs/features/25_observability/03_metrics.md`.

## 22. Audit requirements

Every invocation, successful or not, produces exactly one `AuditEvent` of type `evidence_and_provenance.confidence` conforming to the canonical schema in `docs/schemas/15_audit_event_schema.md` — this file does not redefine the `AuditEvent` field set. `resource_type` is `Document`; `action` is `execute`; `classification` is populated when the resource carries one (`docs/features/20_data_classification/`).

## 23. Performance requirements

p95 < 150ms to resolve a claim's citation chain. Measured and enforced per `docs/performance/01_performance_requirements.md` on the reference hardware profile in `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`. **Status: DESIGN LIMIT** — this budget is an engineering target chosen for demo usability on the reference hardware profile, not yet a benchmark-verified measurement (see `docs/20_DECISION_LOG.md` DEC-014 for the pending validation step). Treat it as a target to test against, not a guaranteed SLA, until DEC-014 is resolved.

## 24. Test requirements

Minimum coverage: one unit test per row in the Failure modes table above, one integration test for the full success path through `/api/v1/evidence-and-provenance/confidence`, and one permission test per role in the table above (three roles × allow/deny = at least 3 assertions), per `docs/testing/01_testing_strategy.md`.

## 25. Acceptance criteria

- [ ] `POST /api/v1/evidence-and-provenance/confidence` succeeds for an `admin` caller with a valid payload and returns the shape in Outputs.
- [ ] The same call is denied per the Permission requirements table for a disallowed role, with the correct error code.
- [ ] Exactly one `evidence_and_provenance.confidence` audit event is produced per invocation, success or failure.
- [ ] The operation completes within the budget stated in Performance requirements on reference hardware.
- [ ] No outbound network call occurs during execution.

## 26. Definition of done

Confidence is done when all Acceptance criteria above pass in CI, the corresponding `docs/schemas/` and `docs/api/` entries match the implementation exactly, and the checklist in `docs/11_DEFINITION_OF_DONE.md` is satisfied.

## 27. Implementation notes

Implement `evidence_and_provenance.confidence` as a single service function called by both the HTTP route and any internal caller (e.g. the agent kernel) — do not duplicate the logic. Reuse the shared RBAC/policy check helper rather than writing a new role comparison; reuse the shared audit-emit helper rather than writing to the audit table directly.

## 28. Forbidden implementations

Do not check `role` via a client-supplied field. Do not perform the `evidence_links` write and the audit write as two separate, independently-failable operations. Do not add a bypass flag (e.g. `skip_approval=true`) reachable from the API. Do not call any host outside `localhost`/internal service addresses from within this operation.

## 29. Examples

**Success:** `admin` calls `POST /api/v1/evidence-and-provenance/confidence` with a valid payload → `200 OK`, `{"status": "ok", "resource_id": "…", "state": "the resulting state (see `docs/runtime/_state_machines_canonical.md`)"}`, one `evidence_and_provenance.confidence` audit event recorded.

**Denied:** `restricted` calls the same endpoint → `403`, `EAP-4030`, audit event recorded with `outcome=denied`.

## 30. Edge cases

Empty/missing `payload` → `400` before any state is touched. Duplicate call with the same `idempotency_key` within the retry window → returns the original result, does not re-execute. Concurrent calls targeting the same `resource_id` → the later call observes the row-level lock and either waits or receives `409`, never a silent lost update. Dependency listed above is degraded but not fully down → Confidence fails closed rather than guessing.
