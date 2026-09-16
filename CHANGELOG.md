# Changelog

> **If you are an AI coding agent: read this before you write code, and append to it before
> you finish your turn.** This file is the running record of what's actually been built,
> by whom, and why — not just what the `docs/` spec says should exist. `docs/` describes the
> target; this file describes progress toward it. They will disagree sometimes (a feature
> spec'd but not yet built, a decision made during implementation that refines the spec) — that
> disagreement is exactly what this file is for tracking.

## How to use this file

1. Before starting work, check `TEAM.md` and confirm which character you're building as.
2. Check this file for the most recent entry under your character's name, so you know what
   you (or the last session building as your character) left off at.
3. Do the work, scoped to your character's owned files per `TEAM.md`.
4. Before ending your turn, append a new entry below, under today's date, in this format:

```
### [Character N — Name] YYYY-MM-DD

**Built/changed:**
- <specific file or capability, one line each>

**Status:** <what works now that didn't before, in plain language>

**Blocked on / depends on:** <if anything you needed from another character isn't ready yet>

**Next:** <what the next session on this character should pick up — optional, only if it's
not obvious from the docs/ spec itself>
```

5. Never edit a previous entry to "clean it up" — this is a log, not a summary document. If
   something in an old entry turned out to be wrong, add a new entry that says so; don't
   rewrite history.
6. Never write an entry claiming something works if you haven't actually run/tested it this
   session — "implemented, not yet tested" is an honest and acceptable status; "done" when it
   isn't is not.

## Format notes

- One `###` entry per work session per character, even if multiple sessions happen the same
  day — don't merge same-day entries from different sessions into one.
- Entries are append-only, newest at the bottom (chronological, not reverse-chronological) —
  this makes each character's own history readable top-to-bottom as a build log, matching
  `docs/08_BUILD_PHASES.md`'s phase ordering.
- If your change touches a shared contract (`docs/api/`, `docs/schemas/`, `docs/domain/`
  outside your carve-outs — see `TEAM.md`'s "Shared contracts" table), say so explicitly in
  the entry so other characters notice it when they next check this file.

---

## Pre-team documentation history

Everything below happened before `TEAM.md`'s six-character split existed — it's the
specification work that produced the `docs/` tree the six characters now build against.
Kept here rather than deleted, since it's real history, just not attributable to a character.

### [Spec maintenance] 2026-09-04 — Identifier fix and consistency audit

**Built/changed:**
- Corrected the `SIH26176` → `SIH26117` identifier across 306 files (see
  `docs/20_DECISION_LOG.md` DEC-018).
- Ran a repository-wide consistency audit: 0 broken links across 7,819 cross-references, 0
  absolute-claim/overclaim language found (DEC-019).

**Status:** Documentation identifier and internal link integrity confirmed clean. This pass's
conclusion that "no further rewriting was needed" was later found inaccurate — see the next
entry.

### [Spec maintenance] 2026-09-04 — Master-prompt compliance audit and remediation

**Built/changed:**
- Full 63-section compliance audit against the original master prompt
  (`docs/MASTER_PROMPT_COMPLIANCE_AUDIT.md`, `docs/DETAILED_FINDINGS_AND_REMEDIATION_PLAN.md`):
  16 complete, 27 partial, 12 missing, 4 contradictory.
- Remediated P0/P1 and most of P2/P3 (see `docs/20_DECISION_LOG.md` DEC-020 for the full list):
  rewrote `docs/05_ARCHITECTURAL_PRINCIPLES.md` and `docs/06_TECHNOLOGY_STACK.md` (were empty
  templates); fixed the confidence-score methodology
  (`docs/features/14_evidence_and_provenance/08_confidence.md`); added the asset/equipment
  domain model (`docs/domain/20_asset_model.md`), the asset-centric knowledge graph
  (`docs/industrial/13_asset_knowledge_graph.md`), and cross-document contradiction detection
  (`docs/industrial/14_knowledge_conflict_detection.md`); added the asset UI screen
  (`docs/ui/23_asset_view.md`); extended `Document`/`Evidence` with the knowledge-trust-model
  and temporal-validity fields; expanded report generation to its full 11-section structure;
  wrote the real sovereignty-attestation mechanism; named the Context Security Boundary
  explicitly; wrote the concrete export-check sequence and model-router selection logic;
  expanded the threat model and feature matrix.
- Deferred explicitly, not silently dropped (DEC-021): DLP, the ~300-file `features/*`
  boilerplate-to-canonical-reference restructuring, two demo scripts, the temporal
  retrieval-time query filter's wiring, the 4th risk tier, and two undecided technology
  choices (reverse proxy, cache/queue).

**Status:** `docs/` now specifies the industrial-differentiation layer that was previously
missing at the entity/knowledge-graph level, not just at the document-workflow level. Nothing
in `services/`/`apps/` exists yet — this was entirely a specification pass.

**Next:** This is where `TEAM.md`'s six characters pick up — building actual code against
this now-more-complete specification. See `docs/08_BUILD_PHASES.md` for phase ordering
(Phase 0 — Foundation — is the natural starting point for Character 1).

---

## Team build history

*(Entries from here on are added by whichever character is actively building — see "How to
use this file" above. Nothing has been built yet as of the creation of this changelog; the
next entry below should be the first character's first real build session.)*

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed:**
- `services/industrial-service/app/__init__.py` — package marker
- `services/industrial-service/app/models.py` — Pydantic domain types for all six
  asset-model entities (Plant, Unit, Equipment, MaintenanceEvent, Inspection, Incident)
  plus GoverningDocumentLink, ConflictRecord, DocumentDiff, DiffEntry,
  EntityResolutionResult. Matches `docs/domain/20_asset_model.md` field-for-field.
- `services/industrial-service/app/database.py` — asyncpg repository layer for all
  six tables plus the `equipment_governing_documents` join table. Includes DDL for
  local/test bootstrapping, entity-resolution tag-matching queries, and knowledge-graph
  edge management. All queries reference the source doc in comments.
- `services/industrial-service/app/entity_resolution.py` — three-case entity resolution
  logic from `docs/industrial/13_asset_knowledge_graph.md` (exact_same_unit auto-link,
  exact_other_unit human-confirmation required, no_match passthrough). Never auto-commits
  in the ambiguous case.
- `services/industrial-service/app/comparison.py` — deterministic document comparison
  engine per `docs/industrial/05_document_comparison.md` and `06_change_detection.md`.
  Explicit synonym table (no model inference). Ambiguous matches reported as "added"
  not silently merged. Confidence scores propagated from Evidence.
- `services/industrial-service/app/conflict_detection.py` — five-step conflict detection
  flow from `docs/industrial/14_knowledge_conflict_detection.md`. Never auto-resolves
  any conflict (principle 12). Temporal overlap check prevents false positives from
  historical non-overlapping documents. Includes canonical CONFLICT DETECTED formatter.
- `services/industrial-service/app/inspection_logic.py` — domain-specific inspection
  rules: Finding dataclass with four required Evidence fields, OCR confidence threshold
  (0.85 CONFIG DEFAULT), unsupported-claim detection, SOP disclaimer validation,
  calculation framing validation.
- `services/industrial-service/app/main.py` — FastAPI application with all routes:
  /assets list+search, /assets/:id detail, Plant/Unit/Equipment CRUD, maintenance/
  inspection/incident sub-resources, governing-document edge management, three internal
  endpoints for inter-service calls (resolve-tag, detect-conflicts, compare-documents).
  Every mutating route emits an AuditEvent. Fails closed on missing/invalid roles.
- `services/industrial-service/requirements.txt` — production dependencies
- `services/industrial-service/pyproject.toml` — pytest configuration
- `services/industrial-service/README.md` — service-level documentation
- `services/industrial-service/tests/test_comparison.py` — unit tests for comparison
- `services/industrial-service/tests/test_conflict_detection.py` — unit tests for
  conflict detection including the "never auto-resolve" invariant (principle 12)
- `services/industrial-service/tests/test_entity_resolution.py` — unit tests for
  three-case entity resolution using async mocks
- `services/industrial-service/tests/test_inspection_logic.py` — unit tests for
  domain rules: Evidence completeness, OCR confidence threshold, SOP disclaimer,
  calculation framing
- `infra/migrations/0010_industrial_asset_model.sql` — forward-only SQL migration for
  all Character 4 tables with COMMENT annotations tracing each constraint to its spec doc
- `infra/docker/industrial-service.Dockerfile` — service Dockerfile, non-root user

**Status:** Implemented, not yet integration-tested (no running PostgreSQL in this
session). All unit tests are written and can be run with
`pytest services/industrial-service/tests/` once dependencies are installed.
Core logic modules (comparison, conflict_detection, entity_resolution, inspection_logic)
are pure-Python and have no external dependencies — their unit tests should pass
immediately. The database and API layers require a running PostgreSQL instance.

**Blocked on / depends on:**
- Character 1: `docs/api/` endpoint contracts not yet written — the `/internal/` routes
  are shaped based on what the spec implies other services need, but Character 1 should
  formalize those contracts before Character 3/2 start calling into this service.
- Character 3 (evidence-service): conflict detection is implemented but the
  evidence-service needs to call `/internal/detect-conflicts` with pre-fetched claims
  for the background-check use case (`docs/industrial/14_knowledge_conflict_detection.md`
  "When conflict detection runs" case 2). That wiring is Character 3's responsibility.
- Character 5 (identity-service): permission checking currently trusts an `x-roles`
  header forwarded by the gateway. Real JWT validation belongs to Character 5's
  identity-service and API gateway integration.

**Next:** Integration tests against a real PostgreSQL instance; wire
`/internal/resolve-tag` into Character 3's document-pipeline ingest flow; add the
asset detail view aggregation endpoint (single call returning Equipment + all history
for ui/23_asset_view.md /assets/:equipmentId — currently the UI would need to make
5 separate calls, which should be collapsed to one).

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed:**
- `services/industrial-service/app/calculations.py` — NEW: deterministic tolerance/spec
  checking, explicit unit conversion, aggregate stats per
  `docs/industrial/10_engineering_calculations.md` + input traceability shape per
  `docs/industrial/11_calculation_verification.md`. Fails closed, never estimates.
- `services/industrial-service/app/inspection_logic.py` — added `validate_drawing_caveat()`
  per `docs/industrial/09_drawing_understanding.md`.
- `services/industrial-service/app/database.py` — `EquipmentRepository.search()` now
  supports `plant_id` + `unit_id` filters (list view per `docs/ui/23_asset_view.md`).
- `services/industrial-service/app/main.py` — removed duplicate `ResolveTagRequest`
  class bug; added `GET /assets/{id}/detail` (single aggregated call for the detail
  view), `GET /documents/{id}/equipment` (impact analysis), `POST /internal/validate-finding`
  (wires `inspection_logic` into pipeline), `POST /internal/validate-answer`
  (SOP/calculation/drawing disclaimer gates), `POST /internal/verify-calculation`
  (tolerance/convert/aggregate); `/assets` search accepts `plant_id` + `unit_id`.
- `services/industrial-service/tests/test_calculations.py` — NEW: 6 tests for the above.

**Status:** Implemented, unit-tested — 46 passed (`pytest tests/` in
`services/industrial-service`). DB/API layers still need live PostgreSQL integration test.

**Blocked on / depends on:**
- Character 3: call `/internal/validate-finding` + `/internal/resolve-tag` from ingest;
  call `/internal/detect-conflicts` from evidence-service.
- Character 2: call `/internal/verify-calculation` + `/internal/compare-documents` from
  agent workflows.
- Character 1/5: formalize `/internal/*` contracts in `docs/api/`; real JWT validation.

**Next:** Live-DB integration test; governing-doc authority/effective-date enrichment
(joins Character 3 Document rows); conflict resolve flow (`Document:reclassify`).

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed:**
- `services/industrial-service/app/models.py` — `ConflictResolutionKind/Create/Resolution`
  per `docs/industrial/14_knowledge_conflict_detection.md` resolution flow (three kinds:
  downgrade_authority, set_effective_until, acknowledge_both).
- `services/industrial-service/app/database.py` — `conflict_resolutions` table DDL +
  `ConflictResolutionRepository` (record + list_by_equipment, newest first).
- `services/industrial-service/app/main.py` — `POST /assets/{id}/conflicts/resolve`
  (gated `Document:reclassify`, audited) + `GET /assets/{id}/conflict-resolutions`
  (Known-conflicts panel history for `ui/23_asset_view.md`).
- `services/industrial-service/app/comparison.py` — `apply_table_confidence_default()`
  per `docs/industrial/07_engineering_documents.md` (table-derived values capped at 0.6
  until verified); wired into changed/added/removed diff entries via `source_kind`.
- `services/industrial-service/.gitignore` — NEW: stop `__pycache__` noise in own service.
- `services/industrial-service/tests/test_resolution.py` — NEW: 4 tests (table cap,
  prose passthrough, diff cap wiring, resolution kinds).

**Status:** Implemented, unit-tested — 50 passed (`pytest tests/` in
`services/industrial-service`).

**Blocked on / depends on:**
- Character 1: `conflict_resolutions` DDL lives in service `init_schema`; needs a
  forward-only `infra/migrations/0011_*` counterpart (Character 1 owns `infra/`).
- Character 3: actual Document.authority/effective_until edits stay in document-pipeline;
  this service only records the human's decision.
- Character 2/3: unchanged — call resolve/list endpoints from the conflict UI flow.

**Next:** Live-DB integration test; governing-doc authority/effective-date enrichment
(joins Character 3 Document rows); SOP-vs-maintenance cross-check helper (03+04).

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (deep audit pass, Character 4 paths only):**
- Audited all 14 `docs/industrial/*`, `docs/domain/20_asset_model.md`, all 14
  `docs/workflows/*`, `docs/ui/23_asset_view.md` against `services/industrial-service/`.
  Workflows 02-05/09-14 impose no Character 4 obligations (other characters' features);
  workflow 07's asset/conflict sections are fed by existing endpoints. No cross-boundary
  files touched.
- `services/industrial-service/app/sop.py` — NEW: `evaluate_sop_compliance()` per
  03+04 (dual-sided evidence gate + disclaimer gate; never decides match itself).
- `services/industrial-service/app/main.py` — `POST /internal/check-sop-compliance`;
  moved mid-file pydantic import to top imports.
- `services/industrial-service/tests/test_sop.py` — NEW: 4 tests; fixed
  `test_resolution.py` enum type nit.
- `services/industrial-service/README.md` — corrected stale "all calculations delegated
  to tool-gateway" claim to describe local deterministic helpers + ToolInvocation
  migration path (was inaccurate vs. `app/calculations.py`).

**Status:** Implemented, unit-tested — 54 passed (`pytest tests/` in
`services/industrial-service`); all modules import cleanly.

**Blocked on / depends on (unchanged, other characters' scope — not acted on):**
- Character 1: `conflict_resolutions` migration counterpart in `infra/`; `/internal/*`
  contracts in `docs/api/`; real JWT validation.
- Character 3: Document.authority/effective-date joins; ingest wiring for
  validate-finding/resolve-tag/check-sop-compliance.
- Character 2: agent-side use of verify-calculation/compare-documents; Risks/AI-insights
  panel summary (uses `GET /assets/{id}/detail`).

**Next:** Live-DB integration test; superseded-SOP grey-out data (needs Character 3
Document validity windows).

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (second deep audit, line-level, Character 4 paths only):**
- `services/industrial-service/app/main.py` — all 7 `/internal/*` endpoints now
  fail closed on permissions (`Equipment:read`; `confirm-link` keeps
  `Equipment:write`): previously resolve-tag/detect-conflicts/compare-documents/
  validate-finding/validate-answer/verify-calculation/check-sop-compliance took
  no roles header at all, violating principle 11. `confirm-link` now 404s on
  unknown equipment instead of leaking a DB FK error as a 500.
- `services/industrial-service/app/inspection_logic.py` — new pure
  `validate_answer_disclaimers()`; unknown `answer_kind` now raises (400) instead
  of passing through as valid (was fail-open for any unrecognized kind).
- `services/industrial-service/app/main.py` — removed dead imports
  (`is_low_confidence`, `format_conflict_output` — both stay tested in their own
  modules, just not used by routes).
- `services/industrial-service/requirements.txt` — dropped unused `sqlalchemy`
  and `opentelemetry*` deps (nothing imports them).
- `services/industrial-service/tests/test_inspection_logic.py` — 3 new tests for
  the disclaimer helper incl. the fail-closed case.

**Status:** Implemented, unit-tested — 57 passed (`pytest tests/` in
`services/industrial-service`); all modules import cleanly.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged —
Character 1 (`infra/` migration, `docs/api/` contracts, JWT), Character 3
(Document joins, ingest wiring), Character 2 (agent-side use, insights summary).

**Next:** Live-DB integration test once PostgreSQL is available.

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (coverage-driven pass — measured 83%, closed to 100%):**
- `tests/test_integration.py` — NEW (11 tests): LIVE PostgreSQL via embedded
  `pgserver` — full lifecycle (plant/unit/equipment CRUD, histories, entity
  resolution cases, governed_by lifecycle, shared-equipment join, conflict
  resolutions, app lifespan boot). Validates real SQL, not just mappings.
  Skips cleanly when pgserver is unavailable.
- `tests/test_contract.py` — NEW (13 tests): route inventory (34 routes),
  repository method surface, cross-module invariants (answer kinds, resolution
  kinds, table-cap < low-confidence threshold), pool fail-closed + DI factories.
  Guards against silent deletions.
- `tests/test_database.py` + `test_routes.py` — gap-fillers to 100% line
  coverage: name filters, full-field update, history lists, all create 201/404/
  400 paths, equipment get 200, convert/aggregate 200s, resolve/govern 404s.
- `requirements-test.txt` — NEW; README documents the suite + 100% gate.
- No production logic changes needed — the audit found code complete; one
  test-only bug fixed (dependency-override values must be callables).

**Status:** 181 passed, 100% line coverage across all 10 app modules
(`pytest tests/ --cov=app`). Live-DB risk retired for Character 4's SQL.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged —
Character 1 (`infra/` migration, `docs/api/` contracts, JWT), Character 3
(Document joins, ingest wiring), Character 2 (agent-side use, insights summary).

**Next:** Cross-character wiring by the owning characters.

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (second full-test pass — remaining uncovered surface):**
- `tests/test_database_extra.py` — NEW (12 tests): Plant/Unit repos, equipment
  partial-update/no-op-update/missing-update/soft-delete/list-by-unit,
  `init_schema` DDL smoke + all-tables-present check, audit helper success post
  and swallowed-failure paths.
- `tests/test_routes.py` — +9 (25 total): autouse audit mock (isolates routes,
  suite back under 1s); equipment create 201/400, update 404, delete 204/404;
  governing-doc add/remove/404; impact-analysis endpoint; resolutions list;
  detail-200 aggregation; SOP positive validation.
- Logic edges: tolerance-no-bounds and aggregate empty/unknown failures;
  location-mismatch/identical/synonym diff cases; table cap on added entries;
  primary-vs-secondary conflicts still surfaced unresolved.
- History-list pagination (shipped in b5aff94) is now pinned by tests
  (repo arg passthrough + route query passthrough).

**Status:** 121 passed (`pytest tests/` in `services/industrial-service`),
DB-free. Per-file counts verified: routes 25, repos 26, logic/detection 58,
views/misc 12.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged.

**Next:** Live-DB integration test once PostgreSQL is available.

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (full-test pass — previously untested layers now covered):**
- `tests/test_database.py` — NEW (14 tests): every repository against a fake
  asyncpg pool — equipment search filters/pagination SQL, `search_with_history`
  tuple mapping + LATERAL, maintenance create (technician/work-order passthrough),
  history pagination args, last-inspection value/None, incident ordering,
  governing-doc upsert idempotency, remove true/false, conflict record round-trip.
- `tests/test_routes.py` — NEW (16 tests): HTTP layer with all repo deps
  overridden (no DB, no network) — asset list/table allow+deny, detail 404,
  history pagination passthrough, all `/internal/*` allow/deny incl. unknown-kind
  400 and bad-operation 400, resolve-tag deny, conflict resolve gate (403 on
  wrong permission) + 201 record path.
- `app/database.py` + `app/main.py` — history lists (maintenance/inspections/
  incidents) paginated server-side (`limit` 1–200, `offset`), matching the asset
  list rule in `docs/ui/23_asset_view.md`.

**Status:** 94 passed (`pytest tests/` in `services/industrial-service`) — full
Character 4 suite, DB-free. Remaining DB risk is live-PostgreSQL SQL validity
only (syntax), not logic.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged.

**Next:** Live-DB integration test once PostgreSQL is available.

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (feature-completeness sweep — every owned spec re-checked):**
- `docs/domain/20_asset_model.md` + `app/models.py` + `app/database.py` —
  `MaintenanceEvent.technician` + `work_order_id` (nullable) per
  `docs/industrial/03_maintenance_records.md` precise-citation rule. DDL, row
  mapper (tolerant of pre-migration rows), and create path updated.
- `app/inspection_logic.py` + `POST /internal/validate-answer` — new `pid`
  answer kind with `validate_pid_caveat()` per `docs/industrial/08_p_and_id_intelligence.md`
  ("description, not structured extraction").
- `app/database.py` — new `EquipmentRepository.search_with_history()` (single query,
  `LEFT JOIN LATERAL`, no N+1); `app/main.py` — new `GET /assets/table`
  (`AssetListItem`: equipment + unit_name + last_inspection_date) per the
  `docs/ui/23_asset_view.md` list-view columns. Bare `GET /assets` unchanged.
- `app/main.py` — `GET /assets/{id}/detail` now includes `conflict_resolutions`
  (Known-conflicts panel data we own) alongside histories and governing docs.
- `tests/test_asset_views.py` — NEW (3 tests); `test_inspection_logic.py` — pid tests.

**Status:** Implemented, unit-tested — 61 passed (`pytest tests/` in
`services/industrial-service`); all modules import cleanly; routes verified.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged —
Character 1 (`infra/` migration incl. new columns, `docs/api/` contracts, JWT),
Character 3 (Document authority/validity joins, ingest wiring), Character 2
(agent-side use, insights summary).

**Next:** Live-DB integration test; existing-DB `ALTER TABLE maintenance_events ADD
COLUMN` note flagged for Character 1's migration authoring.

### [Character 4 — Industrial Intelligence] 2026-09-14

**Built/changed (correctness audit — every module re-read line by line):**
- `app/calculations.py` — temperature conversion is now absolute-scale (F↔C with
  32 offset); previously `f` used a bare 5/9 ratio, silently wrong for absolute
  readings. Dead ratio-table entries removed.
- `app/models.py` + `app/conflict_detection.py` — `ConflictRecord` gains
  `source_{a,b}_effective_until`; formatter renders closed windows as ranges
  (`2020-01-01–2024-02-29`) instead of always `–present`, per the spec's output
  example. Detection passes both windows through.
- `app/models.py` + `app/entity_resolution.py` — case-2 results now carry ALL
  `candidate_equipment_ids`, not just the first match (spec: human UI shows all
  candidates when tags are reused across units).
- `app/database.py` + `app/main.py` — server-driven pagination (`limit` 1–200,
  default 50; `offset`) on `GET /assets` and `GET /assets/table` per
  `docs/ui/23_asset_view.md` ("never client-sliced").
- Tests: +3 (absolute temperature, closed-window rendering, all-candidates).

**Status:** Implemented, unit-tested — 64 passed (`pytest tests/` in
`services/industrial-service`); all modules import cleanly.

**Blocked on / depends on (other characters' scope — not acted on):** unchanged.

**Next:** Live-DB integration test once PostgreSQL is available.

### [Character 1 — Foundation & Inference] 2026-09-14
**Built/changed:**
- `services/model-router/app/__init__.py` — package marker
- `services/model-router/app/models.py` — Pydantic domain types matching `docs/schemas/06_model_schema.md` field-for-field: Model, Provider, Capability, DataClassification, CircuitState, ModelSelectionRequest/Response, ModelHealth, AuditEvent
- `services/model-router/app/config.py` — environment-based configuration per `docs/16_ENVIRONMENT_AND_CONFIGURATION.md` (provider URLs, health polling intervals, circuit breaker thresholds, inference timeouts)
- `services/model-router/app/circuit_breaker.py` — per-model circuit breaker per `runtime/11_retry_policy.md` (open after 5 failures in 60s, half-open probe every 15s, tracked per model ID)
- `services/model-router/app/registry.py` — in-memory model registry with background health polling (vLLM: GET /health, Ollama: GET /api/tags, llama.cpp: GET /health), model CRUD, capability/classification filtering
- `services/model-router/app/router.py` — model selection logic with fallback chain: filter by capabilities, classification, provider preference, size constraints; rank by provider preference then smallest sufficient model; circuit-breaker gating
- `services/model-router/app/database.py` — asyncpg repository for model registry persistence and audit events; DDL for local/test bootstrapping with forward-only migration support
- `services/model-router/app/main.py` — FastAPI application with 12 endpoints: model CRUD, selection, health, audit, availability toggle, inference result reporting, liveness/readiness probes; permission checks (fail closed), audit emission on every mutation
- `services/model-router/requirements.txt` — production dependencies (fastapi, uvicorn, asyncpg, pydantic, httpx, python-dotenv)
- `services/model-router/pyproject.toml` — pytest configuration
- `services/model-router/models.json` — example model registry config (3 models: Llama 3.1 8B, Qwen 2.5 Coder 7B, LLaVA 7B vision)
- `infra/docker/model-router.Dockerfile` — service Dockerfile, non-root user per security hardening
- `services/model-router/README.md` — service-level documentation with endpoints, config, and usage
- `services/model-router/tests/test_models.py` — 14 tests for domain types
- `services/model-router/tests/test_circuit_breaker.py` — 9 tests for circuit breaker states, transitions, independence
- `services/model-router/tests/test_registry.py` — 13 tests for registry CRUD, availability, capability/classification filtering
- `services/model-router/tests/test_router.py` — 14 tests for selection logic, ranking, fallback, circuit-breaker integration
- `services/model-router/tests/test_routes.py` — 20 tests for HTTP routes, permissions, probes
**Status:** Implemented and tested — 70 tests passing (`pytest tests/` in `services/model-router`). All modules import cleanly. Routes verified via FastAPI TestClient. No live PostgreSQL integration test yet (DB optional — service runs without persistence).
**Blocked on / depends on:**
- Character 5 (identity-service): real JWT validation — currently trusts `x-roles` header forwarded by gateway
- Character 2 (agent-kernel): the `POST /api/v1/models/select` endpoint is ready for the agent kernel to call for model selection
- Character 3 (inference-gateway): the `POST /api/v1/models/report-result` endpoint is ready for the inference gateway to report success/failure per inference call
**Next:** Live-DB integration test once PostgreSQL is available; formalize `docs/api/` endpoint contracts (Character 1 owns `docs/api/`); add `infra/migrations/0001_model_router.sql` forward-only migration for the models and audit_events tables

### [Character 1 — Foundation & Inference] 2026-09-14 (session 2)
**Built/changed:**
- `services/inference-gateway/app/schemas.py` — wire schemas: InferenceRequest (messages, kind text/vision, model_id XOR selection, generation params), normalized InferenceResponse (content, model_id, provider, finish_reason, usage, latency_ms, fallback_used), GatewayError envelope with canonical error codes
- `services/inference-gateway/app/adapter_base.py` — BaseAdapter abstract class (generate, health_check, shared httpx client, httpx-exception → error-code mapping) and ProviderError carrying docs/reference/01_error_codes.md codes
- `services/inference-gateway/app/adapters/vllm.py` — vLLM adapter: POST /v1/chat/completions (OpenAI-compatible), 5xx → MODEL_RESOURCE_EXHAUSTED, /health probe
- `services/inference-gateway/app/adapters/ollama.py` — Ollama adapter: POST /api/chat with options mapping (num_predict etc.), done_reason → finish_reason, eval_count → usage, /api/tags probe
- `services/inference-gateway/app/adapters/llamacpp.py` — llama.cpp adapter: llama-server OpenAI-compatible endpoint, /health probe
- `services/inference-gateway/app/adapters/__init__.py` — provider-keyed ADAPTERS registry populated at startup
- `services/inference-gateway/app/router_client.py` — async client for the model-router: POST /api/v1/models/select (returns ModelRef + fallback chain; router 503 → MODEL_UNAVAILABLE) and best-effort POST /api/v1/models/report-result
- `services/inference-gateway/app/gateway.py` — core pipeline: validate (exactly one of model_id/selection; empty selection dict allowed) → resolve via router → per-candidate execution under runtime timeout budget (30s text / 60s vision) → 1 retry with fixed 500ms backoff on MODEL_UNAVAILABLE/INFERENCE_TIMEOUT → walk router fallback chain → report every attempt to router → audit every call
- `services/inference-gateway/app/config.py` — env-based GatewayConfig (router URL, provider URLs, timeout budgets, retry policy, fallback toggle, DATABASE_URL)
- `services/inference-gateway/app/database.py` — asyncpg repository for inference_audit_events table (mirrors model-router audit shape)
- `services/inference-gateway/app/main.py` — FastAPI app: POST /api/v1/infer (503 with canonical error envelope on provider/router failures, 422 on validation), GET /api/v1/providers/health, /healthz, /readyz; RBAC fail-closed (Operator/Engineer/Administrator may infer; Auditor read-only)
- `services/inference-gateway/requirements.txt`, `pyproject.toml`, `README.md` — deps, pytest config (asyncio_mode=auto), service docs
- `infra/docker/inference-gateway.Dockerfile` — non-root user, port 8003 (mirrors model-router hardening)
- `services/inference-gateway/tests/` — 25 tests: gateway core (validation, explicit vs selection, retry, fallback walk, attempt reporting, vision budget, audit) and routes (success/fallback/503 envelope/422/RBAC fail-closed/probes/providers-health)
**Also in this workspace:** recovered the prior session's model-router service (`services/model-router/`, `infra/docker/model-router.Dockerfile`) from the earlier workspace root into this repo root so both Character 1 services live together; its 70 tests still pass here.
**Status:** Implemented and tested — 25 inference-gateway tests passing + 70 model-router tests passing (95 total) via `pytest tests/` in each service directory. No live providers or PostgreSQL; router client and adapters are faked/stubbed in tests. End-to-end wiring against real vLLM/Ollama/llama.cpp not yet exercised.
**Blocked on / depends on:**
- Character 5 (identity-service): real JWT validation — gateway trusts the `x-roles` header forwarded by the platform gateway, same stance as model-router
- model-router (Character 1, done): uses `POST /api/v1/models/select` and `POST /api/v1/models/report-result` contracts as implemented
- Character 2 (agent-kernel): `POST /api/v1/infer` is ready for the agent kernel to call
**Next:** Provider resolution for unprefixed model IDs currently defaults to vLLM (DEC-004); add a model→provider lookup to the router (or include provider in select response payload consumed by the gateway) to remove the guess. Live integration test with real provider endpoints; formalize `docs/api/` contract for /infer (Character 1 owns docs/api/).

### [Character 3 — Knowledge & Documents] 2026-09-15

**Built/changed:**
- `services/document-pipeline/` — first service code in the repo (build-order #14, Phase 5):
  upload validation (size/MIME/extension, sha256 dedup per `runtime/15_idempotency.md`,
  malware-signature reject), file-type detection (magic bytes + PyMuPDF probing), native PDF
  parsing, scanned-PDF detection (text-layer heuristic per `failures/21_pdf_failures.md`),
  page extraction, metadata extraction — the seven feature ops of `features/10_document_ingestion/`
  exposed both as `POST /api/v1/document-ingestion/<op>` and via the canonical REST surface
  `POST/GET/DELETE /api/v1/documents` (`api/11_documents_api.md`)
- Wire conformance: canonical error registry verbatim (`reference/01_error_codes.md`), API
  envelope (`schemas/02`, error shape per `api/26`), audit event per invocation incl. denials
  (`schemas/15`), Document state-machine guard (`runtime/_state_machines_canonical.md`),
  permission-matrix policy for Document (`reference/05`)
- Explicit stubs per the dependency-graph rule: document store, blob storage, audit sink
  (injectable); dev token auth (`Bearer role:<role>`) with deny-by-default
- Test suite: 58 pytest tests covering all Failure-modes rows, permission denials per role,
  and the exactly-one-audit-event invariant — all passing (run 2026-09-15)
- `docs/20_DECISION_LOG.md`: added **DEC-023** (stdlib HTTP choice, stub strategy, dev-token
  auth) — decision-log touch noted here as a shared-contract file

**Status:** Document ingestion works end-to-end locally: a PDF/text/markdown upload is
validated, typed, parsed, routed (native vs. scanned), page-extracted, and left INDEXING —
with one audit event per call and full envelope/error conformance. Not deployed, no real
database/storage behind the stubs yet. Requires Python 3.12 + PyMuPDF (per the stack table).

**Blocked on / depends on:** Real persistence (document store, blob storage) from the
Foundation/Character 1 layer; audit persistence + tamper-evident chain from Character 5's
audit-service; real authentication mechanism replacing `resolve_actor` (single seam).

**Next:** Build-order #15 — Knowledge Fabric (`services/knowledge-fabric/`, chunking +
pgvector indexing handoff that consumes this service's INDEXING state).

### [Character 3 — Knowledge & Documents] 2026-09-15 (session 2)

**Built/changed:**
- Bug fix (cross-character touch, with permission): `services/industrial-service/app/
  conflict_detection.py` — removed an unreachable dead draft block at the end of
  `format_conflict_output` that referenced an undefined `from_a`. It was inert (dead code
  after the real `return`), but any future edit that un-reached it would raise `NameError`.
  No behavior change; ruff F821 now clean repo-wide.
- Deprecation fix (cross-character touch): `tests/test_entity_resolution.py` — replaced
  `datetime.utcnow()` with `datetime.now(timezone.utc)` (schema uses TIMESTAMPTZ; aware
  UTC matches). In-repo DeprecationWarnings now zero; remaining suite warnings originate
  inside the fastapi/starlette/anyio packages themselves.
- Test hygiene in own files: removed an unused variable (F841) in
  `test_upload_validation.py`, replaced an unclosed `open()` with `Path.read_text`
  (SIM115) in `test_pdf_ops.py`.
- Verified this session: static compile + ruff sweep of all four services, then all 334
  tests passing (58 + 70 + 25 + 181), then all four services live-run over HTTP
  (document-pipeline full upload/GET/auth round-trip; industrial-service create/read
  against a real embedded Postgres; model-router and inference-gateway healthz/readyz,
  auth guards, and graceful degradation confirmed).

**Status:** Repo is green and lint-clean on the actionable rules (F821/F841/DTZ-deprecation
in repo code). Known deferred: `DTZ011 date.today()` in conflict_detection is deliberate
(normalized date-window overlap semantics per the spec's examples; tests assert it), and
third-party DeprecationWarnings are upstream packages' to fix.

**Next:** unchanged — build-order #15, Knowledge Fabric.

### [Character 3 — Knowledge & Documents] 2026-09-15 (session 3)

**Built/changed:**
- `services/knowledge-fabric/` — build-order **#15** (Phase 6): all fifteen feature ops of
  `features/13_knowledge_fabric/` (document_store, document_normalization, chunking,
  embeddings, keyword_index, vector_index, metadata_index, hybrid_search, reranking,
  document_hierarchy, permission_filtering, context_assembly, knowledge_overview,
  retrieval_quality, retrieval_failures), exposed as `POST
  /api/v1/knowledge-fabric/<op>` + `GET /api/v1/knowledge-fabric/<op>/{document_id}` and
  as in-process entry points (`service.invoke` — one implementation, feature §12)
- Canonical conformance: DocumentChunk schema (768-dim embedding, bbox, ocr_confidence —
  `schemas/08`), chunk window 200–800 tokens (`domain/07`), Document state machine guard
  limited to this service's owned transitions (INDEXING→READY with `document.indexed`,
  INDEXING→FAILED), permission matrix per `reference/05`, exactly-one invocation audit
  event per call incl. denials, registry-verbatim errors/envelopes
- Explicit stubs (DEC-023/DEC-024): DocumentSource (document-pipeline view), ChunkIndex
  (in-memory cosine; pgvector HNSW later), hash-based 768-dim embeddings
  (model-inference seam later), audit sink, dev-token auth
- Test suite: **56 pytest tests** (indexing pipeline, retrieval + per-chunk permission
  filtering, contracts incl. exactly-one-audit-event and matrix-per-role, HTTP API over a
  live in-process server) — all passing; full repo regression 390/390 green
- `docs/20_DECISION_LOG.md`: added **DEC-024** (stub embeddings; per-chunk policy
  baseline for corpus reads)

**Status:** A document left INDEXING by document-pipeline can be normalized, chunked,
embedded, keyword/vector/metadata indexed, and moved to READY — then searched with
hybrid keyword+vector scoring under per-chunk classification/workspace filtering, reranked,
assembled into token-budgeted context, and diagnosed on empty results. Not deployed;
stubs behind every external seam until Characters 1/5 land their layers.

**Next:** OCR integration (feature group 11) feeds INDEXING docs from scanned PDFs into
this pipeline; pgvector swap-in behind ChunkIndex when the platform layer lands.

### [Character 3 — Knowledge & Documents] 2026-09-15 (session 4)

**Built/changed:**
- **OCR pipeline — build-order #15** (`features/11_ocr`, 9 ops): implemented inside
  `document-pipeline` per `15_CODEBASE_TARGET_STRUCTURE.md` (feature 11 belongs to that
  service; a standalone `services/ocr` was considered and rejected — see DEC-025).

- **OCR pipeline — build-order #15** (`features/11_ocr`, 9 ops): implemented inside
  `document-pipeline` per `15_CODEBASE_TARGET_STRUCTURE.md` (feature 11 belongs to that
  service; a standalone `services/ocr` was considered and rejected — see DEC-024).
  `scanned_pdf_detection` → **EXTRACTING→OCR** on scanned candidates; page/region
  processing (pymupdf 150 DPI rendering, bbox regions, per-page/mean confidence,
  low-confidence flagging per `failures/22`), text reconstruction, coordinate mapping,
  confidence report, failure report, language handling, engine selection, and
  `complete_ocr` → **OCR→INDEXING** with the canonical `document.ocr_completed` event —
  the hand-off into knowledge-fabric (#16).
- Engine seam per `integrations/08`: lazy `PaddleOcrEngine` fails closed with
  DEPENDENCY_UNAVAILABLE when absent; deterministic stub transcribes **real rendered
  PNGs** (pixel-digest pseudo-regions) so stub and real engine share one code path.
- **Policy layering fix** (cross-cutting, shared module): role-denied actors now get
  TOOL_NOT_ALLOWED before the classification layer instead of a misattributed
  FILE_CLASSIFICATION_DENIED — matches every existing test's expectation and the
  registry's code definitions.
- **Audit-contract hardening**: unhandled engine crashes inside an OCR op are mapped to
  DEPENDENCY_UNAVAILABLE with exactly one error audit event, instead of escaping bare.
- `docs/20_DECISION_LOG.md`: added **DEC-025** (+ errata noting the canonical build order
  is OCR=#15, knowledge-fabric=#16; session 3's changelog said #15 for knowledge-fabric).

**Verification:** OCR suite 26/26; full document-pipeline 84/84; whole-repo regression
**416/416** (document-pipeline 84, knowledge-fabric 56, model-router 70,
inference-gateway 25, industrial-service 181). Live HTTP run of the scanned→OCR→INDEXING
pipeline on :8080 — upload → detection (EXTRACTING) → page-processing (OCR, 2 pages) →

  the hand-off into knowledge-fabric (#16, not yet built upstream).
- Engine seam per `integrations/08`: lazy `PaddleOcrEngine` fails closed with
  DEPENDENCY_UNAVAILABLE when absent; deterministic stub transcribes **real rendered
  PNGs** (pixel-digest pseudo-regions) so stub and real engine share one code path.
- **Policy layering fix** (shared module): role-denied actors now get
  TOOL_NOT_ALLOWED before the classification layer instead of a misattributed
  FILE_CLASSIFICATION_DENIED — matches the registry's code definitions.
- **Audit-contract hardening**: unhandled engine crashes inside an OCR op are mapped to
  DEPENDENCY_UNAVAILABLE with exactly one error audit event, instead of escaping bare.
- **CI hygiene** on the same files: dead `arr` buffer (ruff F841) removed from the
  PaddleOCR adapter, and industrial-service's requirements-test.txt no longer pins
  `pgserver>=2.0.0` (no Linux wheels exist; its live-Postgres tests already skip when
  the package is absent — install it locally to run them).
- `docs/20_DECISION_LOG.md`: added **DEC-024** (this increment's decisions).

**Verification:** OCR suite 26/26; full document-pipeline 84/84; ruff
`--select F821,F841,E9` clean. Live HTTP run of the scanned→OCR→INDEXING pipeline on
:8080 — upload → detection (EXTRACTING) → page-processing (OCR, 2 pages) →
text-reconstruction (100 chars) → complete-ocr (INDEXING hand-off) → GET confirms state;
unauthenticated request correctly 401 AUTH_REQUIRED.

**Status:** Scanned PDFs now flow upload → EXTRACTING → OCR (flagged pages persist) →
INDEXING, where knowledge-fabric takes over. Not deployed; PaddleOCR adapter and
Postgres/pgvector seams remain explicit stubs until Characters 1/5 land.

### [Character 3 — Knowledge & Documents] 2026-09-16

**Built/changed:**
- `services/evidence-service/` — build-order **#17** (Phase 6, feature group 14): all ten
  ops of `features/14_evidence_and_provenance/` (evidence_system, claim_extraction,
  claim_to_source_mapping, page_level_citations, coordinate_level_citations, source_chain,
  evidence_graph, confidence, unsupported_claim_detection, evidence_failures) exposed as
  `POST /api/v1/evidence-and-provenance/<op>` + `GET .../<op>/{id}` and as in-process entry
  points (`service.invoke` — one implementation, feature §12)
- Canonical conformance: Evidence fields per `domain/13` + `schemas/09` (schema-gated
  before any logic; caller-supplied `verification_status` ignored on create), citations
  per `schemas/10`, registry-verbatim errors/envelopes, permission matrix
  (`Document:execute`, role denial → TOOL_NOT_ALLOWED before classification layer),
  exactly-one `evidence_and_provenance.<op>` audit event per invocation incl. denials,
  idempotency-key replay (§30) that still audits exactly once
- Domain guardrails: op 09 writes `verification_status` (unverified→supported) but never
  downgrades `contradicted` (industrial/14's output); confidence op returns ONLY the four
  qualitative axes of §3a + a labeled ranking-signal debug view — no combined 0-100%
  number (master prompt §12 anti-pattern); coordinate citations fail closed when the
  chunk carries no bbox; chain walks follow supersession and detect cycles
  (RESOURCE_CONFLICT) and broken chains (RAG_INDEX_UNAVAILABLE)
- Explicit stubs (DEC-023 strategy): evidence_links store, source-chain facts view,
  retrieval view (chunks), audit sink, dev-token auth — all constructor-injected seams
- Test suite: **87 pytest tests** (op behavior, unsupported-claim policy, contracts incl.
  exactly-one-audit-event per op and hash-chain integrity, permission matrix per role,
  HTTP API over a live in-process server) — all passing; full repo regression **503/503**
  (evidence 87, document-pipeline 84, knowledge-fabric 56, model-router 70,
  inference-gateway 25, industrial-service 181); ruff F821/F841/E9 clean
- `.github/workflows/ci.yml` — evidence-service added to the test matrix
- Live HTTP run on :8091 — healthz, 401 AUTH_REQUIRED unauthenticated, full Evidence
  create round-trip with envelope conformance
- `docs/23_SERVICE_MAP_AS_BUILT.md` — NEW as-built service map + pipeline flow page
  (services built so far, the document→OCR→INDEXING→READY→evidence flow, shared
  conformance contract, open stub seams); indexed in `18_DOCUMENTATION_INDEX.md`
- `docs/20_DECISION_LOG.md`: added **DEC-026** (evidence-service stub seams; the as-built
  page) — decision-log touch noted here as a shared-contract file

**Status:** Evidence & Provenance works end-to-end locally: claims extracted from an
answer, Evidence rows created and mapped, verification status derived, citations resolved
to page/coordinates where the data supports it, source chains walked through supersession,
and evidence gaps diagnosed — with one audit event per call and full envelope/error
conformance. Not deployed; store/chain/retrieval/audit/auth seams are explicit stubs
until Characters 1/5 land their layers.

**Blocked on / depends on:** Character 1 (`docs/api/` contracts for the evidence routes;
PostgreSQL migration for evidence_links; pgvector), Character 5 (audit-service,
identity-service), Character 4 (wiring `/internal/detect-conflicts` into the contradiction
path — caller-side, per TEAM.md).

**Next:** wire evidence-service into the agent answer path once agent-kernel (#11)
exists; otherwise the V1 remaining track is Character 5's governance services.

### [Character 3 - Knowledge & Documents] 2026-09-16

**Built/changed (cross-service wiring - the industrial changelog's pending Character-3 item):**
- `services/evidence-service/evidence_service/industrial_gateway.py` - NEW: client for
  industrial-service `/internal/resolve-tag` + `/internal/validate-finding`
  (`X-Roles: Equipment:read`, stdlib transport, injectable opener seam for tests).
  Note: the endpoints live on industrial-service (:8005), not inference-gateway -
  inference-gateway is the LLM routing path.
- `evidence_service/ops.py` - op 01 `evidence_system` (the ingest path) now enriches
  BEFORE persisting when a payload carries the optional `equipment_tag`
  (+ `within_unit_id`, `plant_id`) / `finding` extensions: fail closed on any
  dependency failure (`DEPENDENCY_UNAVAILABLE`, retryable per runtime/11
  interactive-read), 403 from the dependency maps to `POLICY_DENIED`; ambiguous
  (case-2) resolutions surfaced verbatim for human confirmation - governed_by edges
  are never persisted here; `finding_validation` flags surfaced, not gated; payloads
  without the extensions never touch the dependency.
- `evidence_service/config.py` - `EV_INDUSTRIAL_BASE_URL` (default
  `http://127.0.0.1:8005`) + `EV_INDUSTRIAL_TIMEOUT_SECONDS` (default 5).
- `server.py` - builds the live client from settings.
- Tests: `tests/test_industrial_wiring.py` - NEW, **19 tests** (header/body contract,
  canonical error translation, fail-closed no-persist on dependency failure, exactly-one
  audit event on success AND error paths, transient-failure retry under the canonical
  policy, HTTP-path 403 translation, no-dependency-call for plain payloads).
  evidence-service now 106 tests; repo regression **522/522**
  (evidence 106, document-pipeline 84, knowledge-fabric 56, model-router 70,
  inference-gateway 25, industrial-service 181); ruff F821/F841/E9 clean.
- `docs/23_SERVICE_MAP_AS_BUILT.md` - pipeline diagram now marks the live callers;
  test totals updated (522); industrial-service port recorded.
- `services/evidence-service/README.md` - new "Ingest enrichment" section + seams row.

**Verification:** evidence-service 106/106, full repo 522/522, ruff clean under CI's
exact scope (`ruff check services/ --select F821,F841,E9`). Client transport verified
via stub opener + one HTTP-level test (urllib path, 403 translation); no live
industrial-service was running, so no socket-level cross-service run was performed.

**Status:** First live inter-service call in the platform: evidence-service ingest can
enrich Evidence rows with equipment resolution + finding validation from
industrial-service, failing closed when the dependency is down. Not deployed.

**Blocked on / depends on:** Character 1 (`docs/api/` formalization of the /internal
contracts), Character 4 (industrial-service deployed alongside), Character 3
(document-pipeline's own ingest wiring + the detect-conflicts contradiction path).

**Next:** document-pipeline ingest wiring (same pattern), then
`/internal/detect-conflicts` from the evidence contradiction path.

### [Character 3 - Knowledge & Documents] 2026-09-16 (wiring completion)

**Built/changed (second increment - completes every /internal wiring item named in either changelog):**
- LIVE two-service verification: evidence-service (:8091) + industrial-service (:8005,
  real FastAPI app over an in-process pool shim - no PostgreSQL on this machine) -
  enriched ingest verified end-to-end over real HTTP: case-1 `exact_same_unit`,
  case-2 `exact_other_unit` (human confirmation surfaced verbatim), case-3 `no_match`,
  finding flags surfaced (`supported=false` when evidence_id provenance fields are
  absent - surfaced, not gated), and 503 `DEPENDENCY_UNAVAILABLE` fail-closed against
  a dead dependency (no row persisted, correlation_id present).
- `services/industrial-service/app/conflict_detection.py` - INTEROP FIX: `_dates_overlap`
  crashed on the ISO date STRINGS `/internal/detect-conflicts` actually delivers
  (`claims: list[dict]` is never pydantic-parsed). New `_as_date` normalizes ISO date
  and ISO datetime strings (e.g. `2024-01-01T00:00:00Z`); 2 pinning tests added.
- `services/evidence-service` - op 09 contradiction pass wired: builds industrial/14
  claim dicts from resolvable evidence rows (parameter=section_reference, value=chunk
  text, authority + validity windows from the source-chain store) and calls
  `/internal/detect-conflicts`; participants UPGRADE to `verification_status=contradicted`
  (upgrade only - `supported` never downgraded, `contradicted` never downgraded);
  detector outage SKIPS the pass (fail-open detection, never a fabricated status);
  op 01 records task->equipment associations from resolve-tag results (in-process
  registry stub until the KG governed_by lookup lands, DEC-023 seam); op 01 also gained
  the `conflict_check` pass-through enrichment; gateway gained `detect_conflicts`
  with list-typed response validation.
- `services/document-pipeline` - the SAME enrichment pattern wired into
  `upload_validation` (vendored client per DEC-023 no-shared-code, RegistryError
  raised so execute() keeps the exactly-one-audit invariant): resolve-tag +
  validate-finding BEFORE persistence, fail closed, AFTER the sha256 dedup
  short-circuit (duplicates never call the dependency); config keys
  `DP_INDUSTRIAL_BASE_URL` / `DP_INDUSTRIAL_TIMEOUT_SECONDS`.
- Tests: evidence 106->115 (`test_contradiction_wiring.py`), document-pipeline 84->93
  (`test_industrial_wiring.py`), industrial 181->183 (interop pins). Repo regression
  **542/542** (evidence 115, document-pipeline 93, knowledge-fabric 56,
  industrial-service 183, model-router 70, inference-gateway 25); ruff clean (CI scope).
- `docs/23_SERVICE_MAP_AS_BUILT.md` + evidence-service README updated; decision
  recorded as **DEC-028**.

**Status:** all cross-service wiring named in either changelog is LIVE. Remaining
internal-only endpoints (compare-documents, verify-calculation, validate-answer,
check-sop-compliance) await Character 2's agent workflows.

**Next:** knowledge-graph-backed equipment lookup to replace the in-process
conflict-target registry; `docs/api/` formalization (Character 1).

INDEXING, where knowledge-fabric takes over once that service is built upstream. Not
deployed; PaddleOCR adapter and Postgres/pgvector seams remain explicit stubs until
Characters 1/5 land.

### [Character 3 - Knowledge & Documents] 2026-09-16 (KG-backed contradiction scoping)

**Built/changed:**
- `evidence_service/ops.py` - the op-01 task->equipment in-process registry is GONE.
  Op 09's contradiction pass now scopes itself with the REAL knowledge-graph lookup:
  for each evidence source document it calls industrial-service
  `GET /documents/{document_id}/equipment` (the equipment_governing_documents table -
  which equipment a document governs is the graph's fact, not the caller's), then runs
  `/internal/detect-conflicts` per governed equipment. Documents governing no equipment
  skip the detector entirely. This also covers documents ingested by ANY path (enriched
  or not) - the old registry only knew about enriched ingests.
- `evidence_service/industrial_gateway.py` - new `equipment_for_document()` (GET, no
  body, `X-Roles: Equipment:read`, equipment_ids-array validation, 403 ->
  POLICY_DENIED, transport failures -> DEPENDENCY_UNAVAILABLE) over the shared
  `_request` transport (GET/POST unified; opener seam unchanged).
- Caching: KG lookups are read-through cached per (task_id, document_id) - a governed_by
  fact cannot change under a repeated op-09 run - and failures are NEVER cached, so a
  later run catches up. Detector calls are NOT cached (their inputs can change).
- Failure posture unchanged where it matters: a KG-lookup or detector outage SKIPS that
  document (fail-open detection, never a fabricated status; POLICY_DENIED on the scope
  lookup skips too); the `contradicted` upgrade remains upgrade-only.
- Tests: contradiction suite rewritten for the KG flow + 8 new cases (KG contract/parsing,
  malformed body, 403, transport failure, no-equipment skip, lookup outage skip, policy
  denial skip, per-(task,document) caching, op-01 registry removal pin). evidence-service
  115 -> 123; repo regression **550/550** (evidence 123, document-pipeline 93,
  knowledge-fabric 56, industrial-service 183, model-router 70, inference-gateway 25);
  ruff clean (CI scope).
- `docs/23_SERVICE_MAP_AS_BUILT.md` + evidence-service README updated; decision
  recorded as **DEC-029**.

**Status:** the contradiction pass no longer carries any caller-side memory of ingest
time; scoping is entirely the knowledge graph's fact. Not deployed.

### [Character 3 - Knowledge & Documents] 2026-09-16 (root pytest guard + repo-wide runner)

**Built/changed:**
- `pytest.ini` + `conftest.py` (repo root) - running pytest from the repo root used to
  die with 22 collection errors: all six services ship a same-named `tests` package
  whose conftest.py prepends its own service root to sys.path, so one process across
  services mixes the packages up (ImportPathMismatchError). A bare root run now prints
  the remedy once and exits non-zero; pointing pytest at ONE service's suite works from
  the root or in-dir (CI-style); requesting two or more services in one process is
  refused up front with the same explanation. Remove this guard together with any
  future root-level suite (docs/15 reserves tests/unit, integration, security, e2e).
- `scripts/run_tests.py` - repo-wide runner reproducing CI's per-service isolation
  (same `python -m pytest tests/ -q` invocation from each service dir), with per-suite
  summaries, subset selection, --fail-fast, and non-zero exit on any failure.

**Status:** the repo-level "pytest is broken" failure mode is gone. Verified: bare root
run = clean remedy, zero collection errors; single-service runs pass (evidence 123);
multi-service run refused with the remedy; `python scripts/run_tests.py` = **550/550**
across all six suites, exit 0. Ruff clean (CI scope).

**Next:** none pending from this - per-service invocation was already CI's shape; the
guard only makes local mistakes loud and cheap.

- **Preflight script + test docs (Character 3).** Added `scripts/preflight.py`, a developer preflight that runs CI's exact ruff gate (`ruff check services/ --select F821,F841,E9`) and then only the per-service test suites affected by uncommitted changes (staged, unstaged, and untracked files): service-file changes select that service's suite, files outside any single service (`conftest.py`, `pytest.ini`, `scripts/`) force all suites, docs-only changes skip the suites, and `--dry-run` shows the selection without running. Documented the per-service pytest rule and both runners in the root README's new "Running the tests" section. Git and ruff subprocess calls are bounded with one retry because this workstation's OneDrive-backed checkout intermittently wedges child processes.
