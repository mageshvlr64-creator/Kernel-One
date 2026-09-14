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
