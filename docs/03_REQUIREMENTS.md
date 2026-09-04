# Requirements Registry

> **Canonical owner** of every numbered requirement for the Sovereign On-Premise Agentic AI
> Workbench (SIH26176). No other document may define a new requirement ID. Feature and
> architecture documents reference a REQ-ID from this file; they do not restate it.

## How to read this registry

Each requirement has: **ID · Title · Statement · Rationale · Priority · Target · Depends on ·
Acceptance criteria · Verification method · Owning component · Source · Related tests.**

**Priority:** P0 (blocks demo) · P1 (required for a credible V1) · P2 (nice to have in V1).
**Target:** V1 · V2 · Future.

Category prefixes: `REQ-FUNC` functional · `REQ-SEC` security · `REQ-PERF` performance ·
`REQ-DATA` data/storage · `REQ-API` API contract · `REQ-DEP` deployment · `REQ-OPS` operations ·
`REQ-UI` UI · `REQ-AI` agent/model behavior · `REQ-NET` network sovereignty · `REQ-AUD` audit.

---

## REQ-NET — Network Sovereignty

### REQ-NET-001 — Default-deny egress
**Statement:** The default runtime configuration MUST reject all outbound network connections
except to explicitly allowlisted local interfaces (`localhost`, the platform's own internal
service ports, and — only in `restricted` mode — a named, operator-configured allowlist).
**Rationale:** Sovereignty is the product's core differentiator; it must be structurally true,
not a configuration a user can accidentally disable.
**Priority:** P0 · **Target:** V1
**Depends on:** REQ-DEP-003 (container network policy)
**Acceptance criteria:** A network-sovereignty integration test demonstrates zero external
DNS/TCP/HTTP connections during the full reference demo (`docs/demo/01_demo_overview.md`).
**Verification method:** Automated test `TEST-NET-001` (packet capture + DNS log diff, see
`docs/testing/18_network_testing.md`) run in CI against a built container image.
**Owning component:** `features/18_network_sovereignty`
**Source:** Upgrade Prompt §28.
**Related tests:** `TEST-NET-001`, `TEST-NET-002` (air-gapped mode), `SEC-TEST-008`.

### REQ-NET-002 — Three explicit network modes
**Statement:** The system MUST support exactly three named network modes — `air_gapped`
(zero outbound, no DNS resolution at all), `restricted` (outbound limited to an explicit
operator allowlist, e.g. an internal model-mirror registry), and `on_premise` (outbound
limited to the organization's own network, still no public internet) — selected by a single
configuration value at deployment time, not by code changes.
**Rationale:** Different regulated environments need different postures; the mode must be a
deployment-time decision, not an architectural fork.
**Priority:** P0 · **Target:** V1
**Depends on:** REQ-NET-001
**Acceptance criteria:** Switching `NETWORK_MODE` in `docs/16_ENVIRONMENT_AND_CONFIGURATION.md`
changes enforced behavior with no code change and no restart of unrelated services.
**Verification method:** `TEST-NET-003` — deploy same image under all three modes, assert
distinct enforced behavior each time.
**Owning component:** `features/18_network_sovereignty`
**Source:** Upgrade Prompt §28.
**Related tests:** `TEST-NET-003`.

### REQ-NET-003 — Visible, live sovereignty proof
**Statement:** The UI MUST display a live-updating panel showing pass/fail status for
external-egress-blocked checks and internal-service-health checks, refreshed at most every 5
seconds, for the full duration of any session.
**Rationale:** "Trust us" is not acceptable for this product category; the proof must be
observable during the actual demo, not only in a test report.
**Priority:** P0 · **Target:** V1
**Depends on:** REQ-NET-001
**Acceptance criteria:** Panel is visible and updating throughout `docs/demo/01_demo_overview.md`.
**Verification method:** Manual demo walkthrough + `TEST-NET-001` cross-check.
**Owning component:** `features/18_network_sovereignty`, `ui/13_network_panel.md`
**Source:** Upgrade Prompt §28, §41.
**Related tests:** `TEST-NET-001`.

---

## REQ-SEC — Security

### REQ-SEC-001 — Authorization on every state-changing call
**Statement:** Every API endpoint and internal service function that changes persisted state
MUST evaluate the caller's permission via the canonical policy engine
(`reference/05_permission_matrix.md`, `features/21_policy_engine/`) before the state change,
and MUST fail closed (deny) if the policy engine is unreachable.
**Rationale:** A single centrally-enforced check point is the only way ~300 feature surfaces
stay consistent; per-feature ad hoc checks drift and create bypasses.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `SEC-TEST-002`, `SEC-TEST-007` pass; a static-analysis lint
(`docs/58` spec-lint) flags any state-changing route missing a policy-engine call.
**Verification method:** `SEC-TEST-002`, `SEC-TEST-007`, spec-lint rule `LINT-AUTHZ-001`.
**Owning component:** `features/19_identity_and_rbac`, `features/21_policy_engine`
**Source:** Upgrade Prompt §26, §44.
**Related tests:** `SEC-TEST-002`, `SEC-TEST-007`.

### REQ-SEC-002 — Sandbox deny-by-default
**Statement:** Agent- and model-generated code MUST execute only inside the sandbox defined
in `features/09_code_execution/`, with network access denied by default, filesystem access
limited to a per-task mounted workspace directory, and CPU/memory/time limits enforced by the
container runtime (not just application-level checks).
**Rationale:** Code execution is the highest-blast-radius capability in the system.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `SEC-TEST-003` (generated code attempts network access) fails to
reach any host outside `localhost`.
**Verification method:** `SEC-TEST-003`, `TEST-SANDBOX-001..004` (`docs/testing/14_sandbox_testing.md`).
**Owning component:** `features/09_code_execution`
**Source:** Upgrade Prompt §19, §44.
**Related tests:** `SEC-TEST-003`.

### REQ-SEC-003 — Prompt-injection containment
**Statement:** Content retrieved from documents, tool output, or web-adjacent sources (where
permitted by network mode) MUST be marked as untrusted context distinct from system/developer
instructions, and the agent kernel MUST NOT grant tool-invocation authority based solely on
instructions found inside untrusted context.
**Rationale:** Retrieved-content prompt injection is the most realistic attack path against an
agent that reads uploaded documents.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `SEC-TEST-004` (document with embedded injection attempting to
trigger an unauthorized tool call) does not result in the tool call executing.
**Verification method:** `SEC-TEST-004`.
**Owning component:** `features/04_agent_kernel`, `security/05_prompt_injection.md`
**Source:** Upgrade Prompt §29, §44.
**Related tests:** `SEC-TEST-004`.

### REQ-SEC-004 — Path traversal prevention
**Statement:** Every filesystem-touching tool call MUST resolve the requested path against the
task's workspace root and reject (not silently clamp) any path that resolves outside it,
including via symlinks.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `SEC-TEST-005` passes.
**Verification method:** `SEC-TEST-005`.
**Owning component:** `features/06_filesystem_tool`
**Source:** Upgrade Prompt §29, §44.
**Related tests:** `SEC-TEST-005`.

### REQ-SEC-005 — Audit tamper-evidence
**Statement:** Audit events MUST be append-only at the storage layer (no `UPDATE`/`DELETE`
grant on the audit table for any application role) and each event's integrity MUST be
verifiable via a hash chain (each event stores the hash of the previous event).
**Priority:** P1 · **Target:** V1
**Acceptance criteria:** Attempting to modify a past audit row via the application's own DB
credentials fails at the database privilege level, not only the application level.
**Verification method:** `TEST-AUDIT-002` (`docs/testing/17_audit_testing.md`).
**Owning component:** `features/17_audit`
**Source:** Upgrade Prompt §30, §44.
**Related tests:** `TEST-AUDIT-002`.

---

## REQ-FUNC — Functional

### REQ-FUNC-001 — Document ingestion and evidence-grounded Q&A
**Statement:** A user MUST be able to upload a scanned, multi-page PDF; have it OCR'd,
chunked, and indexed locally; ask a natural-language question about its contents; and receive
an answer where every factual claim carries a citation resolving to a specific page (and, for
native PDFs, a bounding box) in the source document.
**Priority:** P0 · **Target:** V1
**Depends on:** REQ-FUNC-004 (RAG), REQ-FUNC-005 (evidence model), REQ-AI-002 (OCR)
**Acceptance criteria:** `docs/demo/05_inspection_report_demo.md` scenario completes with
every claim in the agent's answer resolving to a real citation.
**Verification method:** `TEST-E2E-001`.
**Owning component:** `features/10_document_ingestion`, `features/13_knowledge_fabric`,
`features/14_evidence_and_provenance`
**Source:** Upgrade Prompt §20, §22, §23, §41.
**Related tests:** `TEST-E2E-001`.

### REQ-FUNC-002 — Autonomous multi-step task execution
**Statement:** The agent kernel MUST be able to decompose a natural-language task into a plan
of at most `AGENT_MAX_STEPS` (config default: 20) tool-invocation steps, execute them in
order (or replan on step failure up to `AGENT_MAX_REPLANS`, config default: 3), and produce a
final artifact or textual response.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `docs/demo/06_coding_agent_demo.md` scenario completes without manual
intervention beyond required approvals.
**Verification method:** `TEST-E2E-002`.
**Owning component:** `features/04_agent_kernel`
**Source:** Upgrade Prompt §17, §41.
**Related tests:** `TEST-E2E-002`.

### REQ-FUNC-003 — Human approval gate on high-risk actions
**Statement:** Any action classified `high` risk in `reference/03_risk_levels.md` (code
execution against non-read-only mounts, external export, destructive file operations,
privileged config change) MUST pause and require an explicit `approve`/`reject` decision from
a user holding the `Administrator` or `Security Officer` role before executing.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** A high-risk plan step does not execute until an approval record with
`decision=approved` exists for it.
**Verification method:** `TEST-APPROVAL-001`.
**Owning component:** `features/16_human_approval`
**Source:** Upgrade Prompt §25, §44.
**Related tests:** `TEST-APPROVAL-001`.

### REQ-FUNC-004 — Local hybrid retrieval
**Statement:** The knowledge fabric MUST combine vector similarity search (pgvector, cosine
distance) and keyword/full-text search (PostgreSQL `tsvector`) into a single ranked result
set, filtered by the caller's classification and workspace access BEFORE ranking, not after.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `SEC-TEST-001` (unauthorized retrieval attempt) returns zero results
from the restricted document, not a filtered-after-the-fact result.
**Verification method:** `TEST-RAG-003`, `SEC-TEST-001`.
**Owning component:** `features/13_knowledge_fabric`
**Source:** Upgrade Prompt §22.
**Related tests:** `SEC-TEST-001`, `TEST-RAG-003`.

### REQ-FUNC-005 — Evidence model with no fabricated citations
**Statement:** Every citation attached to an agent claim MUST reference an `Evidence` record
containing `source_document_id`, `document_version`, `page`, `chunk_id`, `source_hash`, and
`retrieval_method`; the agent kernel MUST refuse to emit a claim it cannot attach evidence to
rather than emit an unsupported claim.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `TEST-EVIDENCE-001` — every citation in a sampled set of 20 agent
answers resolves to a real, matching source passage.
**Verification method:** `TEST-EVIDENCE-001`.
**Owning component:** `features/14_evidence_and_provenance`
**Source:** Upgrade Prompt §23.
**Related tests:** `TEST-EVIDENCE-001`.

---

## REQ-AI — Agent / Model Behavior

### REQ-AI-001 — Model-agnostic routing
**Statement:** The model router MUST select a model based on declared capability
(`schemas/06_model_schema.md`), not a hardcoded model name; swapping the underlying model
referenced by a capability MUST require only a registry entry change, not code change.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `TEST-ROUTER-004` swaps the "coding" capability's backing model via
config only and the coding demo still passes.
**Verification method:** `TEST-ROUTER-004`.
**Owning component:** `features/02_model_router`
**Source:** Upgrade Prompt §12 (Rule 12), §8.
**Related tests:** `TEST-ROUTER-004`.

### REQ-AI-002 — OCR fallback for scanned documents
**Statement:** Document ingestion MUST detect whether a PDF page contains an extractable text
layer; if not (page text-character density below 5% of page area — CONFIG DEFAULT, not
benchmarked), it MUST route that page through the OCR engine before indexing.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** The reference scanned inspection report demo page (`docs/demo/03_demo_data.md`)
is fully indexed and searchable.
**Verification method:** `TEST-OCR-001`.
**Owning component:** `features/11_ocr`
**Source:** Upgrade Prompt §20.
**Related tests:** `TEST-OCR-001`.

### REQ-AI-003 — MoE storage vs. active-parameter distinction documented and enforced
**Statement:** The model registry (`features/01_model_management/01_model_registry.md`)
MUST record, for any Mixture-of-Experts model, both `total_parameters` (governs disk/VRAM
storage requirement) and `active_parameters_per_token` (governs per-token compute), and the
hardware-fit check in the model router MUST evaluate storage against `total_parameters`, never
against `active_parameters_per_token`.
**Rationale:** This exact confusion is a common, costly deployment mistake (Rule 13).
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `TEST-ROUTER-005` — a router hardware-fit check correctly rejects an
MoE model whose `total_parameters` storage exceeds available VRAM even though
`active_parameters_per_token` would fit.
**Verification method:** `TEST-ROUTER-005`.
**Owning component:** `features/01_model_management`, `features/02_model_router`
**Source:** Upgrade Prompt §7, Rule 13.
**Related tests:** `TEST-ROUTER-005`.

---

## REQ-PERF — Performance

### REQ-PERF-001 — Reference-hardware demo latency
**Statement:** On `PROFILE-B` (`docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`), the
end-to-end inspection-report demo (upload → OCR → index → answer with citation) MUST complete
in under 5 minutes wall-clock for a 10-page scanned document. **Status: DESIGN LIMIT** (chosen
as a demo-usability threshold; not yet benchmark-verified against final model selection —
see `20_DECISION_LOG.md` DEC-014).
**Priority:** P1 · **Target:** V1
**Verification method:** `TEST-PERF-001`, manual stopwatch at first rehearsal.
**Owning component:** cross-cutting
**Source:** Upgrade Prompt §50, §6.
**Related tests:** `TEST-PERF-001`.

---

## REQ-DATA — Data / Storage

### REQ-DATA-001 — Classification propagation
**Statement:** A document's classification level MUST propagate to every `DocumentChunk`,
`Evidence`, and `Artifact` derived from it; an artifact MUST inherit the highest classification
level among all evidence it cites.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `TEST-CLASS-001` — an artifact generated from CONFIDENTIAL and
INTERNAL evidence is itself tagged CONFIDENTIAL.
**Verification method:** `TEST-CLASS-001`.
**Owning component:** `features/20_data_classification`
**Source:** Upgrade Prompt §27.
**Related tests:** `TEST-CLASS-001`.

---

## REQ-AUD — Audit

### REQ-AUD-001 — Universal audit coverage
**Statement:** Every mutation to `Task`, `ToolInvocation`, `Approval`, `Artifact`, `Document`,
`User`, `Role`, and `SystemConfiguration` MUST produce exactly one `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same logical transaction as the mutation.
**Priority:** P0 · **Target:** V1
**Acceptance criteria:** `TEST-AUDIT-001` — for a scripted sequence of 50 mixed operations,
audit event count equals mutation count exactly.
**Verification method:** `TEST-AUDIT-001`.
**Owning component:** `features/17_audit`
**Source:** Upgrade Prompt §30.
**Related tests:** `TEST-AUDIT-001`.

---

## Open / undecided requirements

### REQ-PERF-002 — Concurrent user count — **DECISION REQUIRED**
V1 target concurrency (1 user? 5? 20?) has not been decided; it materially changes
PROFILE-C/D sizing. Owner: product lead. Status: open, see `20_DECISION_LOG.md` DEC-015.

### REQ-DEP-004 — Multi-node V1 support — **DECISION REQUIRED**
Whether V1 must support the multi-node topology (`architecture/16_multi_node_architecture.md`)
or whether that is entirely V2 is not yet decided. Current default assumption (see
`02_SCOPE_AND_NON_GOALS.md`) is single-node-only for V1; this entry exists so the assumption
is visible and challengeable rather than implicit.

---

## Requirement → Component → Test summary table

| REQ ID | Owning component | Primary test(s) |
|---|---|---|
| REQ-NET-001 | features/18_network_sovereignty | TEST-NET-001 |
| REQ-NET-002 | features/18_network_sovereignty | TEST-NET-003 |
| REQ-NET-003 | features/18_network_sovereignty, ui/13_network_panel | TEST-NET-001 |
| REQ-SEC-001 | features/19_identity_and_rbac, features/21_policy_engine | SEC-TEST-002, SEC-TEST-007 |
| REQ-SEC-002 | features/09_code_execution | SEC-TEST-003 |
| REQ-SEC-003 | features/04_agent_kernel | SEC-TEST-004 |
| REQ-SEC-004 | features/06_filesystem_tool | SEC-TEST-005 |
| REQ-SEC-005 | features/17_audit | TEST-AUDIT-002 |
| REQ-FUNC-001 | features/10_document_ingestion, 13_knowledge_fabric, 14_evidence_and_provenance | TEST-E2E-001 |
| REQ-FUNC-002 | features/04_agent_kernel | TEST-E2E-002 |
| REQ-FUNC-003 | features/16_human_approval | TEST-APPROVAL-001 |
| REQ-FUNC-004 | features/13_knowledge_fabric | SEC-TEST-001, TEST-RAG-003 |
| REQ-FUNC-005 | features/14_evidence_and_provenance | TEST-EVIDENCE-001 |
| REQ-AI-001 | features/02_model_router | TEST-ROUTER-004 |
| REQ-AI-002 | features/11_ocr | TEST-OCR-001 |
| REQ-AI-003 | features/01_model_management, 02_model_router | TEST-ROUTER-005 |
| REQ-PERF-001 | cross-cutting | TEST-PERF-001 |
| REQ-DATA-001 | features/20_data_classification | TEST-CLASS-001 |
| REQ-AUD-001 | features/17_audit | TEST-AUDIT-001 |

This table is generated from, and must stay consistent with, the entries above — if you add a
requirement, add its row here in the same change.
