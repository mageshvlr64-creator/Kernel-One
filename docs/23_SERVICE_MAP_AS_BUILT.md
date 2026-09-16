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

**Snapshot date: 2026-09-16** (build order through #17, plus Character 4's
parallel industrial track).

## 2. Service map (what exists)

| Service (`services/`) | Character | Feature groups implemented | Build order | Tests | Notes |
|---|---|---|---|---|---|
| `model-router/` | 1 — Foundation & Inference | 01 model management, 02 model router | #6/#8 | 70 | registry, selection + fallback chain, per-model circuit breaker |
| `inference-gateway/` | 1 — Foundation & Inference | 03 inference gateway (one provider path) | #7 | 25 | provider adapters (vLLM/Ollama/llama.cpp shapes), retry + fallback walk |
| `document-pipeline/` | 3 — Knowledge & Documents | 10 document ingestion, 11 OCR | #14, #15 | 84 | upload→parse→OCR→INDEXING; scanned-PDF path live over HTTP |
| `knowledge-fabric/` | 3 — Knowledge & Documents | 13 knowledge fabric | #16 | 56 | chunk → embed → index → hybrid search → context assembly |
| `evidence-service/` | 3 — Knowledge & Documents | 14 evidence and provenance | #17 | 87 | Evidence rows, claims, citations, source chains, confidence axes, unsupported-claim detection |
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
 │        supported; `contradicted` is conflict detection's to write)       │
 │     → page_level_citations / coordinate_level_citations                  │
 │        (Source → Version → Page → Chunk → bbox)                          │
 │     → source_chain (supersession walk) → evidence_graph                  │
 │     → confidence (four qualitative axes — never a bare %)                │
 │     → evidence_failures (structured diagnosis)                           │
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
                    Character 4 — industrial-service
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ cross-checks over Evidence/Document rows via its /internal/* endpoints:  │
 │ validate-finding, detect-conflicts, compare-documents,                   │
 │ validate-answer, verify-calculation, check-sop-compliance, resolve-tag   │
 │ (Character 3's services are the callers of record for the wiring; the    │
 │ HTTP contracts exist and are tested)                                     │
 └──────────────────────────────────────────────────────────────────────────┘
```

Parallel to this, Character 1's inference path (model-router `:8002` ↔
inference-gateway `:8003`, per the service Dockerfiles) serves model selection
and `POST /api/v1/infer`; the agent-kernel that would orchestrate across both
paths is build order #11 — not built.

Wiring still pending between built services (each owned by the caller's
character, per `TEAM.md`): document-pipeline → industrial-service
`/internal/resolve-tag` + `/internal/validate-finding` calls during ingest;
evidence-service → industrial-service `/internal/detect-conflicts` for the
contradiction path.

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
| industrial-service | (uvicorn) | `uvicorn app.main:app` | `pytest tests/` in `services/industrial-service` |

CI (`.github/workflows/ci.yml`) lints all services with ruff (F821/F841/E9) and
runs each service's suite in its own matrix job. Current repo total: **503
passing tests** (84 + 56 + 87 + 70 + 25 + 181), ruff clean.

## 6. Open seams (what is deliberately not real yet)

| Seam | Stub today | Real version lands with |
|---|---|---|
| Authentication | dev bearer tokens, server-side actor records | identity-service (Character 5, build #3) |
| Audit storage | in-memory hash-chained sink | audit-service (Character 5, build #5) |
| Persistence | in-process stores per service | PostgreSQL migrations (Character 1 `infra/`) |
| Vector index | brute-force cosine over in-memory chunks | pgvector HNSW (Character 1 `infra/`) |
| Embeddings | deterministic hash vectors | model-inference seam (Character 1) |
| OCR engine | deterministic stub on real rendered PNGs | PaddleOCR adapter (`integrations/08`) |
| Inter-service calls | seeded in-process views of other services' data | documented `docs/api/` contracts (Character 1) |
| Permission decisions | in-process matrix mirror | policy-engine (Character 5, build #4) |

## 7. Maintenance

- This page is updated in the same change that adds or materially changes a
  service (rule 2) — including test counts and the snapshot date.
- New as-built decisions get a `20_DECISION_LOG.md` entry (rule 9); this page's
  creation is DEC-026.
- It does not replace `CHANGELOG.md` (the per-session build log) or
  `08_BUILD_ORDER.md` (the target ordering) — it summarizes the distance
  between them.
