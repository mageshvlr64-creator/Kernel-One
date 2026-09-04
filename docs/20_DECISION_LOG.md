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
