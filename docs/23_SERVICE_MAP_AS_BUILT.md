# Service Map As Built

> Root status document · `docs/23_SERVICE_MAP_AS_BUILT.md`
> Previous: `22_REFACTOR_AUDIT_REPORT.md` · Next: —
> **Status type: as-built snapshot.** The `features/` tree is the *target*
> specification; this page is the *progress* record. Where they disagree, both
> are buggy by rule 2 (`13_DEVELOPER_RULES.md`) — the fix is either more code or
> an honest update here, in the same change.

## 1. Purpose

The six-character build (`../TEAM.md`) is producing services incrementally, and
the spec tree does not say which parts exist yet. This page maps what is
actually built — service by service, with the pipeline flow as it runs today —
so any contributor (human or AI) can orient without diffing `CHANGELOG.md`
against the build order. It is updated in the same change that adds or changes a
service, and every claim here is backed by a `CHANGELOG.md` entry.

**Snapshot date: 2026-09-16** (build order through #17, Character 4's
parallel industrial track, and ALL THREE named cross-service wiring items now
live over real HTTP: evidence-service ingest → `/internal/resolve-tag` +
`/internal/validate-finding`; evidence-service op 09 → KG lookup +
`/internal/detect-conflicts` (contradiction pass, scoped by the real
knowledge graph — no in-process registry); document-pipeline upload →
`/internal/resolve-tag` + `/internal/validate-finding`. Verified end-to-end
with both services running: case-1/case-2 resolution, finding flags, fail-closed
on dependency outage, `contradicted` upgrade through the detector).

## 2. Service map (what exists)

| Service (`services/`) | Character | Feature groups implemented | Build order | Tests | Notes |
|---|---|---|---|---|---|
| `model-router/` | 1 — Foundation & Inference | 01 model management, 02 model router | #6/#8 | 70 | registry, selection + fallback chain, per-model circuit breaker |
| `inference-gateway/` | 1 — Foundation & Inference | 03 inference gateway (one provider path) | #7 | 25 | provider adapters (vLLM/Ollama/llama.cpp shapes), retry + fallback walk |
| `document-pipeline/` | 3 — Knowledge & Documents | 10 document ingestion, 11 OCR | #14, #15 | 94 | upload→parse→OCR→INDEXING; scanned-PDF path live over HTTP; upload calls industrial `/internal/resolve-tag` + `/internal/validate-finding` (fail-closed enrichment, after sha256 dedup) |
| `knowledge-fabric/` | 3 — Knowledge & Documents | 13 knowledge fabric | #16 | 57 | chunk → embed → index → hybrid search → context assembly |
| `evidence-service/` | 3 — Knowledge & Documents | 14 evidence and provenance | #17 | 122 | Evidence rows, claims, citations, source chains, confidence axes, unsupported-claim detection; ingest enrichment + op-09 contradiction pass scoped by the real KG lookup (both live, fail-closed/fail-open respectively) |
| `industrial-service/` | 4 — Industrial Intelligence | industrial/* (assets, comparison, conflicts, calculations, SOP) | parallel track | 181 | 7 `/internal/*` endpoints, all fail closed on permissions |

Not yet built (no `services/` directory, per build order #3–#5, #9–#13, #18+):
identity-service, policy-engine, audit-service, tool-gateway, calculator tool,
agent-kernel, filesystem tool, code execution, human approval, artifact engine,
network-monitor, and the Character 6 platform services (admin console,
observability, backup, memory, spreadsheet). Until identity-service and
audit-service exist, every built service runs the documented dev-token auth and
in-memory audit sink (DEC-023).

## 3. Pipeline flow as built

The document-to-evidence flow that works end-to-end today (all transitions per
`runtime/_state_machines_canonical.md#document`):

```
                    Character 3 — document-pipeline (:8080)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ upload_validation → UPLOADED                                             │
 │   file_type_detection → VALIDATING                                       │
 │     native_pdf_parsing → EXTRACTING        (native PDFs)                 │
 │     scanned_pdf_detection → EXTRACTING → OCR   (scanned PDFs, #15)       │
 │       page/region processing → text reconstruction → complete_ocr        │
 │         (document.ocr_completed, low-confidence pages flagged)           │
 │           → INDEXING                                                     │
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
                    Character 3 — knowledge-fabric (:8090)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ document_store → normalization → chunking (200–800 tokens)               │
 │   → embeddings (768-dim stub) → keyword/vector/metadata index            │
 │     → (document.indexed) INDEXING → READY                                │
 │ retrieval: hybrid_search → reranking → context_assembly                  │
 │   (per-chunk classification + workspace filtering, never unfiltered)     │
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
                    Character 3 — evidence-service (:8091)   [#17]
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ claim_extraction (answer → spans + claims)                               │
 │   → evidence_system / claim_to_source_mapping (Evidence rows, schemas/09)│
 │     → unsupported_claim_detection (verification_status: unverified →     │
 │        supported; → contradicted via industrial /internal/detect-conflicts│
 │        scoped by the REAL knowledge-graph lookup (GET                    │
 │        /documents/{id}/equipment) — upgrade only, fail-open if the       │
 │        graph or detector is down; detection never auto-resolves,         │
 │        humans do)                                                        │
 │     → page_level_citations / coordinate_level_citations                  │
 │        (Source → Version → Page → Chunk → bbox)                          │
 │     → source_chain (supersession walk) → evidence_graph                  │
 │     → confidence (four qualitative axes — never a bare %)                │
 │     → evidence_failures (structured diagnosis)                           │
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
                    Character 4 — industrial-service (:8005)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ cross-checks over Evidence/Document rows via its /internal/* endpoints:  │
 │ validate-finding, detect-conflicts, compare-documents,                   │
 │ validate-answer, verify-calculation, check-sop-compliance, resolve-tag   │
 │ LIVE callers today (all wiring named in the changelogs is done):         │
 │  • evidence-service op 01 → resolve-tag + validate-finding (fail closed) │
 │  • evidence-service op 09 → KG lookup (GET /documents/{id}/equipment)    │
 │    + detect-conflicts (contradiction pass; participants become           │
 │    `contradicted`; fail-open on dependency outage)                       │
 │  • document-pipeline upload → resolve-tag + validate-finding             │
 │    (fail closed, after the sha256 dedup short-circuit)                   │
 │ Still internal-only: compare-documents, verify-calculation,              │
 │ validate-answer, check-sop-compliance (Character 2 caller not built).    │
 └──────────────────────────────────────────────────────────────────────────┘
```

Parallel to this, Character 1's inference path (model-router `:8002` ↔
inference-gateway `:8003`, per the service Dockerfiles) serves model selection
and `POST /api/v1/infer`; the agent-kernel that would orchestrate across both
paths is build order #11 — not built.

Wiring status between built services (each owned by the caller's character,
per `TEAM.md`): all three named items are now LIVE — document-pipeline →
industrial-service `/internal/resolve-tag` + `/internal/validate-finding`
during upload; evidence-service → `/internal/detect-conflicts` for the
contradiction path (op 09); evidence-service ingest → `/internal/resolve-tag`
+ `/internal/validate-finding`. The first live cross-service HTTP call landed
with evidence-service ingest; verified end-to-end with both services running
(entity resolution cases 1–3, finding flags surfaced, 503 fail-closed, and the
contradiction upgrade to `contradicted` through the real detector).

## 4. Conformance contract every built service implements

All six services share the same canonical plumbing — this is the platform's
de-facto integration contract until Character 1's `docs/api/` and Character 5's
services land:

- **Errors:** exclusively from `reference/01_error_codes.md`, verbatim user
  messages; unregistered codes fail loud at construction.
- **Envelope:** success `{"data": ...}`, error
  `{"error": {code, message, details, correlation_id}}` (`schemas/02`, `api/26`).
- **Audit:** exactly one `AuditEvent` per invocation — success, error, or denial
  — per `schemas/15`, hash-chained in the sink stub; denials record the
  caller's role and the specific denying rule.
- **Policy:** canonical `reference/05_permission_matrix.md` rows with layered
  classification/workspace checks; role denial short-circuits as
  `TOOL_NOT_ALLOWED` before the classification layer (DEC-025 item 4); roles
  come from server-side actor records only (§28 of every feature doc).
- **State machines:** only the owner-legal transitions of
  `runtime/_state_machines_canonical.md`; foreign transitions raise
  `RESOURCE_CONFLICT`.
- **Retry:** canonical classes from `runtime/11_retry_policy.md` (same helper
  shape in every service).
- **Auth:** dev bearer tokens (`Bearer dev-token-<role>`), deny-by-default —
  DEC-023, replaced by identity-service later.
- **Stubs:** every external dependency is a constructor-injected seam with
  production semantics documented at the seam — never a silent fake.

## 5. Running the built services

| Service | Port (dev default) | Run | Test |
|---|---|---|---|
| document-pipeline | 8080 | `python server.py` | `pytest tests/` in `services/document-pipeline` |
| knowledge-fabric | 8090 | `python server.py` | `pytest tests/` in `services/knowledge-fabric` |
| evidence-service | 8091 | `python server.py` | `pytest tests/` in `services/evidence-service` |
| model-router | 8002 | `python -m app` or Dockerfile | `pytest tests/` in `services/model-router` |
| inference-gateway | 8003 | `python -m app` or Dockerfile | `pytest tests/` in `services/inference-gateway` |
| industrial-service | 8005 | `uvicorn app.main:app --port 8005` | `pytest tests/` in `services/industrial-service` |

CI (`.github/workflows/ci.yml`) lints all services with ruff (F821/F841/E9) and
runs each service's suite in its own matrix job. Current repo total: **584
passing tests** (123 + 94 + 57 + 183 + 102 + 25), ruff clean.

## 6. Open seams (what is deliberately not real yet)

| Seam | Stub today | Real version lands with |
|---|---|---|
| Authentication | dev bearer tokens, server-side actor records | identity-service (Character 5, build #3) |
| Audit storage | in-memory hash-chained sink | audit-service (Character 5, build #5) |
| Persistence | in-process stores per service | PostgreSQL migrations (Character 1 `infra/`) |
| Vector index | brute-force cosine over in-memory chunks | pgvector HNSW (Character 1 `infra/`) |
| Embeddings | deterministic hash vectors | model-inference seam (Character 1) |
| OCR engine | deterministic stub on real rendered PNGs | PaddleOCR adapter (`integrations/08`) |
| Inter-service calls | evidence + document-pipeline ingest → industrial `/internal/*` are live HTTP clients, and op 09's contradiction pass reads the real KG (`GET /documents/{id}/equipment`); all other cross-service reads are seeded in-process views | documented `docs/api/` contracts (Character 1) |
| Permission decisions | in-process matrix mirror | policy-engine (Character 5, build #4) |

## 7. Maintenance

- This page is updated in the same change that adds or materially changes a
  service (rule 2) — including test counts and the snapshot date.
- New as-built decisions get a `20_DECISION_LOG.md` entry (rule 9); this page's
  creation is DEC-026.
- It does not replace `CHANGELOG.md` (the per-session build log) or
  `08_BUILD_ORDER.md` (the target ordering) — it summarizes the distance
  between them.
