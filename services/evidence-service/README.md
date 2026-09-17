# evidence-service

Evidence & Provenance (feature group 14, build-order **#17**, Phase 6) — ties every
claim an agent makes back to a specific source: Evidence rows, page- and
coordinate-level citations, source chains, the four-axis confidence
representation, and unsupported-claim detection.

Character 3 (Knowledge & Documents) owns this service, per `TEAM.md`.

## Ops (one per feature doc, §12 single-implementation rule)

| Route (`POST /api/v1/evidence-and-provenance/<op>`) | Feature file | What it does |
|---|---|---|
| `evidence_system` | `01_evidence_system.md` | create an Evidence row (schemas/09 validated) + optional industrial-service enrichment (see below) |
| `claim_extraction` | `02_claim_extraction.md` | segment an agent answer into spans + claims |
| `claim_to_source_mapping` | `03_claim_to_source_mapping.md` | link a claim to its supporting Evidence |
| `page_level_citations` | `04_page_level_citations.md` | Source → Version → Page citation |
| `coordinate_level_citations` | `05_coordinate_level_citations.md` | page + bbox citation (needs chunk coordinates) |
| `source_chain` | `06_source_chain.md` | walk Source → Version → Page/Section → Chunk, following supersession |
| `evidence_graph` | `07_evidence_graph.md` | claims/evidence/sources graph for a task |
| `confidence` | `08_confidence.md` | four qualitative axes — **never** a single 0–100% number (§3a anti-pattern) |
| `unsupported_claim_detection` | `09_unsupported_claim_detection.md` | claims without Evidence rows; sets `verification_status` (upgrade only: unverified→supported→contradicted via industrial `/internal/detect-conflicts`) |
| `evidence_failures` | `10_evidence_failures.md` | structured diagnosis (broken chain, superseded source, missing page/coords, pending verification) |

Read paths: `GET /api/v1/evidence-and-provenance/<op>/{id}` (evidence_id,
claim_id, or task_id depending on the op) plus unauthenticated `GET /healthz`.

## Ingest enrichment (live cross-service wiring)

Op 01 (`evidence_system`) doubles as the ingest path: when a payload carries the
optional `equipment_tag` (+ `within_unit_id`, `plant_id`), `finding`, or
`conflict_check` extensions, evidence-service calls industrial-service's
`/internal/resolve-tag`, `/internal/validate-finding`, and
`/internal/detect-conflicts` (`industrial_gateway.py`) **before** persisting
the Evidence row:

- enrichment failure (transport, timeout, non-2xx) fails closed —
  `DEPENDENCY_UNAVAILABLE`, no row persisted; a 403 from the dependency
  translates to `POLICY_DENIED`;
- ambiguous (case-2) tag resolutions are surfaced verbatim
  (`requires_human_confirmation`) — governed_by edges are never persisted here;
- `finding_validation` flags (`supported`, `ocr_warning`) are surfaced, not gated;
- payloads without the extensions never touch the dependency.

### Contradiction pass (op 09 → KG lookup + `/internal/detect-conflicts`)

For each of a task's evidence source documents, op 09
(`unsupported_claim_detection`) first asks industrial-service's **real
knowledge graph** which equipment that document governs
(`GET /documents/{id}/equipment`, backed by its `equipment_governing_documents`
table): scoping is the graph's fact, not ours — no in-process registry
substitutes for it, and it covers documents ingested by *any* path, enriched
or not. Documents that govern no equipment are skipped without touching the
detector. For the rest it runs industrial's deterministic conflict detector
over the task's resolvable evidence rows: parameter = section reference,
value = chunk text, authority + validity windows from the source-chain store.
Every row whose source document participates in a `ConflictRecord` is
upgraded to `verification_status: contradicted` — an upgrade only
(`supported` is never downgraded; nothing downgrades `contradicted`).

Failure posture: a KG-lookup or detector outage **skips that document** —
detection failure must never fabricate a status; the next op-09 run catches
up. KG lookups are read-through cached per (task, document) — a graph fact
cannot change under a repeated op-09 run — and failures are never cached.
The detector itself never auto-resolves; human review resolves (industrial/14).

Config: `EV_INDUSTRIAL_BASE_URL` (default `http://127.0.0.1:8005`),
`EV_INDUSTRIAL_TIMEOUT_SECONDS` (default 5).

## Contracts honored

- Permission matrix: `Document:execute` — Administrator / Security Officer /
  Operator / Analyst; Restricted User and Auditor denied (`TOOL_NOT_ALLOWED`),
  layered classification/workspace checks per `reference/05_permission_matrix.md`.
- Errors exclusively from `reference/01_error_codes.md`, verbatim messages,
  envelope per `schemas/02` + `api/26`.
- Exactly one `evidence_and_provenance.<op>` audit event per invocation —
  success, error, or denial — schema `schemas/15`, hash-chained in the stub sink.
- Evidence field contract: `domain/13_evidence_model.md` + `schemas/09`;
  citations per `schemas/10`. `verification_status` is written only by op 09;
  `contradicted` is conflict-detection's output and is never downgraded.
- Idempotency: `idempotency_key` replays return the original result without
  re-executing (feature docs §30 edge case).

## Stubs (DEC-023 strategy — replaced via constructor injection)

| Seam | Stub now | Replaced later by |
|---|---|---|
| evidence_links store | in-process dict | PostgreSQL table (Character 1 `infra/`) |
| source-chain facts | seeded in-process view | document-pipeline documents API |
| chunk coordinates | seeded in-process view | knowledge-fabric API |
| audit sink | in-memory, hash-chained | audit-service (Character 5) |
| auth | dev bearer tokens | identity-service (Character 5) |
| industrial enrichment client | **live HTTP client** (`industrial_gateway.py`) | n/a — first real inter-service call; `docs/api/` formalization pending (Character 1) |

## Tests

```bash
cd services/evidence-service
python -m pytest tests/ -q
```

Coverage maps to the feature docs' Test requirements (§24) and Acceptance
criteria (§25): unit tests per Failure-modes row, integration tests per success
path, permission tests per role, the exactly-one-audit-event invariant, the
industrial enrichment wiring (header/body contract, error translation,
fail-closed persistence, retry, HTTP path), and the op-09 contradiction pass
(KG-scoped, contradicted upgrade, never-downgrade, fail-open detection,
caching). **122 tests.**
