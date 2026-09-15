# Decision Log (ADR Register)

> Every non-trivial architecture decision is recorded here with date, status, context,
> options considered, and rationale. If a decision has not actually been made, it is marked
> **DECISION REQUIRED** with an owner — it is never silently assumed elsewhere in the docs.

Format: `DEC-###` · Date · Status (`Proposed`/`Accepted`/`Superseded`/`Decision Required`) ·
Context · Options · Decision · Rationale · Consequences · Rejected alternatives.

---

### DEC-001 — Single-node-first architecture for V1
**Date:** 2026-08-15 · **Status:** Accepted
**Context:** The system must be demonstrable on a single workstation for SIH while remaining
extensible to multi-node production deployments.
**Options:** (a) Design multi-node from day one; (b) design single-node with clean service
boundaries that generalize later.
**Decision:** (b). All services run as separate processes/containers on one host for V1;
service boundaries follow `architecture/06_service_boundaries.md` so they can be redistributed
later without a rewrite.
**Consequences:** V1 cannot demonstrate horizontal scaling; `architecture/16_multi_node_architecture.md`
remains a design document, not a tested configuration, until V2.
**Rejected:** Full Kubernetes-based multi-node from day one — rejected as disproportionate
engineering cost for a 14-day build cycle with a single-machine demo requirement.

### DEC-002 — PostgreSQL + pgvector over a dedicated vector database
**Date:** 2026-08-15 · **Status:** Accepted
**Context:** Need both relational storage (users, tasks, approvals, audit) and vector search
(RAG) without operating two separate database systems on constrained hardware.
**Options:** (a) PostgreSQL + pgvector extension; (b) PostgreSQL + a separate vector DB
(Qdrant/Milvus/Weaviate); (c) SQLite + a lightweight vector index (FAISS) for the smallest
deployments.
**Decision:** (a) for PROFILE-B/C/D; PostgreSQL is the single database technology.
**Rationale:** One database to operate, back up, and secure is a meaningful operational win
for a sovereignty-focused product where the operator is often not a dedicated DBA team.
pgvector's HNSW index is adequate at V1's expected corpus size (tens of thousands of chunks).
**Consequences:** If corpus size grows into the millions of chunks, a dedicated vector DB may
be revisited (tracked as a V2+ item in `later/`).
**Rejected:** SQLite — rejected because it lacks the concurrent-write and role-based access
control characteristics needed once RBAC/classification filtering is applied at query time.

### DEC-003 — MinIO for object storage
**Date:** 2026-08-16 · **Status:** Accepted
**Context:** Need to store original uploaded documents and generated artifacts outside the
relational database.
**Options:** (a) MinIO (S3-compatible, self-hostable); (b) plain filesystem storage with a
path convention; (c) a cloud object store.
**Decision:** (a) MinIO for PROFILE-B+; plain filesystem storage remains an allowed
`OPTIONAL` substitute for PROFILE-A local development only.
**Rationale:** S3-compatible API gives a clean abstraction boundary and a realistic path to
multi-node later, while still running entirely on-prem.
**Rejected:** Cloud object storage — categorically excluded by REQ-NET-001/002.

### DEC-004 — vLLM as primary inference runtime, Ollama/llama.cpp as fallback
**Date:** 2026-08-17 · **Status:** Accepted
**Context:** Need a model runtime that works on PROFILE-B (single consumer GPU) and scales to
PROFILE-C/D.
**Options:** (a) vLLM only; (b) vLLM primary + Ollama/llama.cpp fallback for
CPU-only/lower-VRAM cases; (c) llama.cpp only.
**Decision:** (b). The inference gateway (`features/03_inference_gateway/`) abstracts all
three behind one interface; vLLM is used when a compatible GPU is present, llama.cpp/Ollama
cover CPU-only (PROFILE-A) and quick local iteration.
**Rationale:** vLLM's throughput matters at PROFILE-C/D concurrency; llama.cpp's CPU path
matters for REQ-AI's `cpu-fallback` requirement.
**Consequences:** The gateway must maintain provider-specific adapters (`03_vllm_provider.md`,
`04_ollama_provider.md`, `05_llamacpp_provider.md`) — added complexity accepted for the
resilience it buys.

### DEC-005 — Docker/Firejail sandbox for code execution
**Date:** 2026-08-18 · **Status:** Accepted
**Context:** Agent- and model-generated code must run isolated from the host.
**Options:** (a) Docker container per execution, network disabled; (b) Firejail namespace
isolation; (c) gVisor/Kata for stronger isolation.
**Decision:** (a) Docker as the default V1 mechanism, with Firejail as an OPTIONAL
lighter-weight alternative on hosts where Docker-in-Docker is undesirable.
**Rationale:** Docker's `--network=none` plus per-container CPU/memory cgroup limits meet
REQ-SEC-002 with tooling every target operator already has.
**Rejected:** gVisor/Kata — stronger isolation but adds an operational dependency
disproportionate to V1's threat model; tracked as a V2+ hardening option in `later/`.

### DEC-006 — Two-role V1 RBAC, six-role canonical model
**Date:** 2026-08-19 · **Status:** Accepted (superseded scope note)
**Context:** The canonical permission matrix (`reference/05_permission_matrix.md`) defines six
roles (Administrator, Security Officer, Operator, Analyst, Restricted User, Auditor), but a
14-day V1 build cannot fully exercise all six in the demo.
**Decision:** The **permission matrix itself defines all six roles** as the canonical target
model (so schemas/API/policy engine are built correctly from the start), but the V1 demo
exercises only `Administrator` and `Restricted User` end-to-end. The other four roles exist in
the schema and policy engine but are not demo-critical paths.
**Rationale:** Building the schema for six roles costs little extra; building and rehearsing
six distinct demo flows costs a lot. This decision keeps the data model honest without
inflating demo scope.
**Consequences:** `Security Officer`, `Operator`, `Analyst`, and `Auditor` flows are
implemented but not polished/rehearsed for V1 demo purposes.

### DEC-007 — Append-only audit table with hash chain, no separate SIEM in V1
**Date:** 2026-08-20 · **Status:** Accepted
**Context:** Need tamper-evident audit (REQ-SEC-005) without operating a separate SIEM stack.
**Decision:** Hash-chained rows in the primary PostgreSQL database, with `INSERT`-only grants,
is sufficient for V1. Export to an external SIEM is a V2+ integration
(`later/` — not yet filed as a specific item; add if requested).
**Rejected:** Standalone append-only log store (e.g. a WORM-configured object store) —
higher operational cost not justified for V1's single-node target.

---

### DEC-018 — Canonical project identifier corrected to SIH26117
**Date:** 2026-09-04 · **Status:** Accepted
**Context:** A full-repository audit found the entire `docs/` tree (306 files) consistently used
the identifier `SIH26176` instead of the officially intended `SIH26117`, including in the title
of `00_README.md`, `18_DOCUMENTATION_INDEX.md`, every `features/*` file, and all cross-references.
No file used the correct identifier prior to this pass.
**Options:** (a) Leave both identifiers in place and treat it as cosmetic; (b) do a repository-wide
find-and-replace to a single canonical identifier.
**Decision:** (b). Every occurrence of `SIH26176` was replaced with `SIH26117`. No filenames
contained the stale identifier, so no files required renaming.
**Consequences:** All 306 previously-affected files now read consistently. Any external
references (submission portal, prior slide decks, repo name) that still say SIH26176 must be
updated to match, or this decision reversed — see repository-wide audit note below.
**Rejected:** Keeping two identifiers "for compatibility" — rejected per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §3, which explicitly disallows silently preserving both.

### DEC-019 — Repository-wide consistency audit (identifier, links, overclaim language)
**Date:** 2026-09-04 · **Status:** Accepted
**Context:** Per the refactor master prompt's final-audit requirement (§59), the tree was
scanned programmatically for: stale identifiers, broken internal doc references (both
markdown-style `[]()` links and backtick path references), banned absolute/overclaim
language (`100% secure`, `hallucination-free`, `fully autonomous`, `guaranteed`, etc.), and
features marked simultaneously MVP and future.
**Findings:** 0 broken links across 7,819 internal cross-references; 0 unresolved overclaim
phrases (the few hits on "guaranteed" were all hedged, rollback-safety language, not marketing
claims); 0 features found double-flagged as both MVP and V2/future — `reference/10_feature_matrix.md`
already resolves this cleanly. The only substantive issue found was DEC-018 (identifier).
**Decision:** No further large-scale rewriting was needed to satisfy §59; the documentation set
was already internally consistent. This entry serves as the audit record required by §60(D).
**Consequences:** Future contributors should re-run this same class of check (identifier grep,
link check, overclaim grep) before any large documentation merge, rather than assuming the tree
stays consistent by hand.

### DEC-020 — Master-prompt compliance remediation (first pass)
**Date:** 2026-09-04 · **Status:** Accepted
**Context:** A section-by-section compliance audit against
`SIH26117_Documentation_Refactor_Master_Prompt.txt`'s 63 sections (see
`MASTER_PROMPT_COMPLIANCE_AUDIT.md`, `DETAILED_FINDINGS_AND_REMEDIATION_PLAN.md`) found 12
MISSING, 4 CONTRADICTORY, and 27 PARTIAL items — correcting DEC-019's conclusion that no
further rewriting was needed.
**Decision:** Remediate in the priority order the audit's remediation plan set out (P0
architectural contradictions, then P1 core industrial differentiation), rather than
alphabetically or file-by-file. This entry records what was actually done in this pass; see
DEC-021 for what was explicitly deferred.
**Changes made, P0 (critical contradictions):**
- `05_ARCHITECTURAL_PRINCIPLES.md` rewritten with the 15 real principles (was empty boilerplate).
- `06_TECHNOLOGY_STACK.md` rewritten with the actual stack table, assembled from
  `integrations/*.md` and DEC-002 through DEC-007 (was empty boilerplate).
- `features/14_evidence_and_provenance/08_confidence.md` rewritten: replaced the bare
  0.0-1.0 confidence score's unexplained presentation with a documented methodology
  (Evidence Coverage/Source Authority/Freshness/Cross-Source Agreement, no combined fake-precision number).
- `22_REFACTOR_AUDIT_REPORT.md` given a superseding note pointing to the corrected findings.
**Changes made, P1 (core industrial differentiation):**
- New `domain/20_asset_model.md` — Plant/Unit/Equipment/MaintenanceEvent/Inspection/Incident
  entities, relational (no new database), referenced from `domain/01_domain_model.md`.
- New `industrial/13_asset_knowledge_graph.md` — the `governed_by`/`extracted_from`/`supersedes`
  relationship model, entity resolution (tag matching), provenance, temporal validity.
- New `industrial/14_knowledge_conflict_detection.md` — cross-document contradiction detection
  between independent authoritative sources (distinct from `06_change_detection.md`'s
  same-lineage revision diffing) and its human-resolution flow.
- `domain/13_evidence_model.md` extended with `section_reference`, `source_authority`,
  `verification_status` fields.
- `domain/06_document_model.md` extended with `authority`, `effective_from`,
  `effective_until`, `superseded_by` fields — the knowledge-trust-model and temporal-validity
  fields the master prompt's §37/§38 required; retrieval-time filtering on these fields is
  noted as a follow-on implementation item, not yet wired into the default query path.
- New `ui/23_asset_view.md` — the equipment/asset screen; wired into `ui/03_navigation.md`
  along with new Workflows and Reports routes.
- `04_SYSTEM_ARCHITECTURE.md` updated to name Industrial Intelligence as an explicit branch
  of the Capability layer, and given a §34 coverage-map section.
- `workflows/07_report_generation.md` expanded from a 3-step stub to the full 11-section
  report structure, with the two sections depending on the above (Affected assets, Detected
  conflicts) marked with honest population-status notes rather than claimed complete.
- `19_GLOSSARY.md` given the 5 missing terms (Asset, Claim, Revision, Verification, Reranking).
- `08_BUILD_PHASES.md` given a new Phase 6.5 — Industrial Intelligence, so this work is
  trackable in the build plan going forward.
**Changes made, P2/P3 (security, sovereignty, documentation):**
- `features/18_network_sovereignty/12_sovereignty_status.md` given a real attestation
  mechanism (four checks: outbound connection audit, DNS audit, per-integration reachability,
  mode-consistency) replacing its boilerplate body.
- `ui/13_network_panel.md` aligned to the master prompt's exact sovereignty-status field
  vocabulary (Mode/Internet/External AI/Local Models/Local Knowledge/Network Attestation).
- `architecture/09_trust_boundaries.md` given an explicit, named Context Security Boundary
  section tying together the identity→permissions→documents→evidence→tools→models→artifacts→
  exports chain, which previously existed only as separately-correct individual hops.
- `features/20_data_classification/11_export_restrictions.md` given the concrete 5-step
  export check sequence (permissions→classification→destination→policy→approval), replacing
  boilerplate.
- `features/02_model_router/01_router_overview.md` given the actual selection logic (hard
  gates for capability/policy/resource, weighted scoring for accuracy/latency among survivors).
- `security/02_threat_model.md` given Likelihood and Residual Risk columns, plus 5 new threat
  entries (Compromised Local User, Unauthorized Model Access, Malicious Generated Artifacts,
  Poisoned Knowledge, Stale Documents) that were named in the master prompt but absent.
- `reference/03_risk_levels.md` given an explicit justification for keeping 3 risk tiers
  instead of the master prompt's suggested 4, tied to V1 having no direct operational-control
  actions (see DEC-021 for revisiting this if that scope changes).
- `reference/10_feature_matrix.md` rewritten to the 5-tier (CORE MVP/V1/V1.5/FUTURE/RESEARCH)
  vocabulary and the 6-column format the master prompt specified, one row per capability
  instead of grouped ranges.
- `00_README.md` opening rewritten to lead with the industrial-intelligence framing instead
  of the generic-agentic-workbench framing.
- Verified (no change needed): `schemas/15_audit_event_schema.md` already has a
  `prev_event_hash` field — the audit hash chain was already real, not templated, contrary to
  this audit's initial "not independently verified" flag. `performance/02_latency_budgets.md`
  and `07_concurrency_limits.md` already have concrete sandbox timeout/concurrency numbers.

### DEC-021 — Explicitly deferred items from the compliance remediation
**Date:** 2026-09-04 · **Status:** Accepted (deferral, not a rejection)
**Context:** Not every finding from `DETAILED_FINDINGS_AND_REMEDIATION_PLAN.md` was addressed
in DEC-020's pass — some are genuinely large (a 300-file mechanical restructuring) or blocked
on product decisions this audit shouldn't make unilaterally.
**Deferred, with reason:**
- **DLP (input-side scanning), master prompt §23:** no feature group exists for this. Rather
  than invent one or silently drop it, it's recorded here as an explicit V1 gap. Revisit if
  SIH judging criteria specifically probe security depth here.
- **§33/§58 — the ~300-file `features/*` boilerplate-to-canonical-reference restructuring:**
  large, mechanical, not blocking any specific demo capability. A template fix should be
  prototyped on 2-3 files and reviewed before a full rollout, not done unilaterally across 300
  files in one pass.
- **§27 demo-directory renumbering** (coding-agent/spreadsheet demos as peers of the flagship
  industrial demos rather than a supporting-capabilities appendix): a labeling/organization
  change, deferred pending a decision on whether the demo script itself is being finalized
  soon (better to do this once, alongside final demo-script edits).
- **§50 Demo 3 (contradiction) and Demo 4 (asset trace) demo scripts:** the underlying features
  now have specifications (`industrial/14_knowledge_conflict_detection.md`,
  `ui/23_asset_view.md`), but writing the demo scripts themselves is left for implementation
  time, once there's a working system to script a walkthrough against.
- **§38's retrieval-time temporal filter:** the schema fields exist
  (`domain/06_document_model.md`), but wiring a dated-query filter into
  `features/13_knowledge_fabric/09_hybrid_search.md`'s actual query logic is implementation
  work, not a documentation change — noted as a tracked follow-on there.
- **4th (CRITICAL) risk tier:** see the reasoning added directly to `reference/03_risk_levels.md`
  — deferred, not rejected, pending V1 scope actually including direct operational-control
  actions.
- **Reverse proxy and cache/queue technology choices** (`06_TECHNOLOGY_STACK.md`'s two OPEN
  rows): no technology was named for either, since no existing file committed to one — naming
  one here would have been inventing a choice, which this audit was explicitly told not to do.

### DEC-022 — Six-character team split and agent-maintained changelog
**Date:** 2026-09-05 · **Status:** Accepted
**Context:** Building this system with multiple people/AI agent sessions in parallel risks
constant file collisions if ownership isn't explicit. The existing
`15_CODEBASE_TARGET_STRUCTURE.md` maps features to services 1:1 already, but nothing assigned
those services to a bounded group of builders, and nothing tracked build progress separately
from the specification itself.
**Decision:** Added `TEAM.md` (repo root, sibling to `docs/`) defining six non-overlapping
ownership zones (Foundation & Inference; Agent Kernel & Tools; Knowledge & Documents;
Industrial Intelligence; Security/Governance/Sovereignty; Platform UI/Ops/Delivery), each with
an explicit "Owns" list covering both `docs/` spec paths and `services/`/`apps/`/`packages/`
code paths, plus a "Shared contracts" table for the handful of files (domain/schemas/api/
reference tables) everyone reads but only one character edits. Added `CHANGELOG.md` (repo
root) as the agent-maintained build log, distinct from the spec: `docs/` says what should
exist, `CHANGELOG.md` says what actually has been built, by which character, and what it
depends on.
**Also:** extended `15_CODEBASE_TARGET_STRUCTURE.md` with three services that had specs but no
assigned service directory (`spreadsheet-service`, `observability-service`, `backup-service`)
and one new one for this pass's own additions (`industrial-service`, backing
`industrial/*`/`domain/20_asset_model.md`) — needed so Character 4 and Character 6 had a real
code path to own, not just a docs path.
**Consequences:** Any agent asked to write code should read `TEAM.md` first and ask which
character it's building as, per the instruction block at that file's top. `00_README.md` and
`18_DOCUMENTATION_INDEX.md` updated to point to both new files.
**Rejected:** A single shared `TODO.md` with no ownership split — rejected because it doesn't
solve the actual problem (agents editing the same files simultaneously); assigning by feature
number alone without also assigning the corresponding `services/` code path — rejected because
half the point is preventing collisions in the actual codebase, not just the spec.

### DEC-023 — Document-pipeline first increment: stdlib HTTP, explicit stubs, dev token auth
**Date:** 2026-09-15 · **Status:** Accepted · **Owner:** Character 3 (Knowledge & Documents)
**Context:** `services/document-pipeline/` is the first code built in the repo (build-order
item #14, Phase 5). Three foundations were unspecified by the spec and had to be chosen now:

1. **HTTP layer.** The stack table (`06_TECHNOLOGY_STACK.md`) pins Python and PyMuPDF but
   names no HTTP framework, and no `docs/api/` file commits to one. The first increment uses
   the standard library (`http.server` + a thin route table in `document_pipeline/api.py`)
   rather than pulling FastAPI/uvicorn into a brand-new service with no other service yet
   deployed beside it. The wire shape is fully envelope-conformant either way, so migrating
   to a framework later is a contained change behind the ops layer.
2. **Unbuilt dependencies.** Per the dependency-graph rule, document-pipeline's dependencies
   (document store, blob storage, audit sink) do not exist yet — no other service does. They
   are explicit, labeled stubs (`document_pipeline/storage.py`, the in-memory store in
   `store.py`, the injectable audit sink in `audit.py`) that the consuming service will
   replace; they never silently fake behavior the spec requires (e.g. the tamper-evident
   audit chain is Character 5's audit-service concern and is deliberately not implemented
   here).
3. **Authentication for tests/dev.** The permission matrix (`reference/05`) pins role→
   Document decisions but the spec does not yet spec an authentication mechanism (the API
   contract's `actor` is a shape, not a mechanism). The service resolves actors from dev
   bearer tokens of the form `Authorization: Bearer role:<role>` and DENIES everything it
   cannot resolve (AUTH_REQUIRED), so no request is ever treated as implicitly authorized.
   Real authn replaces `resolve_actor` in one place.

**Decision:** All three as described. `/healthz` is deliberately unauthenticated (liveness
probe); every other route requires a resolvable actor and enforces the canonical matrix.
**Consequences:** First framework decision to revisit when Character 1's platform layer lands
or a second service needs to share HTTP middleware (correlation ids, audit-on-deny, envelope
serialization currently live per-service). Stub seams are narrow and documented in each
module's docstring so replacement is mechanical.
**Rejected:** Waiting for a platform team to pick the HTTP framework before any service code
exists — rejected because it serializes all six characters behind one unspecified choice and
the spec's own build order has document ingestion in Phase 5, ahead of any such decision.

## Open decisions (DECISION REQUIRED)

### DEC-013 — Exact model checkpoints to pin for V1 demo
**Status:** Decision Required · **Owner:** Product/ML lead
Which specific open-weight checkpoints back each `ModelCapability` slot in
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s reference model registry has not been finalized.
Blocking: final PROFILE-B latency numbers (REQ-PERF-001), final `model-inference` timeout
values (`runtime/11_retry_policy.md`).

### DEC-014 — Benchmark validation of PROFILE-B latency targets
**Status:** Decision Required · **Owner:** Engineering lead
`REQ-PERF-001`'s 5-minute end-to-end target and the 30s/60s `model-inference` timeouts are
DESIGN LIMIT / CONFIG DEFAULT values, not yet benchmarked against a pinned model (blocked by
DEC-013). Must be re-validated once DEC-013 is resolved, before Build Phase 10 hardening.

### DEC-015 — V1 target concurrent user count
**Status:** Decision Required · **Owner:** Product lead
See `REQ-PERF-002`. Affects whether PROFILE-B alone is an acceptable V1 production target or
whether PROFILE-C sizing must be validated before calling V1 "done."

### DEC-016 — Multi-node support in or out of V1
**Status:** Decision Required · **Owner:** Product lead
See `REQ-DEP-004`. Current working assumption (documented in `02_SCOPE_AND_NON_GOALS.md`) is
"out of V1" — this entry exists so that assumption is a visible, challengeable decision, not
an implicit one.

### DEC-017 — External SIEM/log export integration
**Status:** Decision Required · **Owner:** Security lead
Not currently scoped for V1 or explicitly deferred to V2 — needs an explicit call once a
target deployment's compliance requirements are known.
