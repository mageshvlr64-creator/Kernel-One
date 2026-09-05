# SIH26117 — Detailed Compliance Findings (MISSING / CONTRADICTORY / PARTIAL)

> Expands the summary matrix from the prior audit into full evidence per item, per your
> request. **No files were modified to produce this document.** Every "exact section/header"
> below was read directly from the file in this pass or the immediately preceding one — not
> inferred from a filename.

---

## PART 1 — MISSING (12 items)

### §6 — Industrial entity model (Org→Plant→Unit→Equipment→Maintenance/Inspection/Incidents)

1. **Requirement:** Explicit conceptual model with Plant/Unit/Equipment/Maintenance/Inspection/Incident as first-class entities under Organization.
2. **File(s):** `docs/domain/01_domain_model.md`, `docs/industrial/01_industrial_intelligence_overview.md`
3. **Section/header:** `domain/01_domain_model.md` § "Entity list and owning file" (the full entity table)
4. **Why MISSING:** The entity table lists exactly 16 entities: Workspace, Organization, User, Role, Document, DocumentChunk, Model, ModelDeployment, ModelCapability, AgentRun, Tool, ToolInvocation, TaskStep, Task, Conversation, Message, Evidence, Citation, Artifact, Approval, Policy, AuditEvent, MemoryEntry, ClassificationLevel. None of Plant/Unit/Equipment/Asset/MaintenanceEvent/Inspection/Incident appear. `industrial/01_industrial_intelligence_overview.md` states outright: *"nothing here introduces new infrastructure; it defines domain-specific workflows and expectations on top of existing features"* — a direct, explicit statement that no new entities exist.
5. **Current status:** 0% — no schema, no field table, no relationship diagram.
6. **Affects MVP:** **Yes.** Blocks §7 (knowledge graph), §43 (asset UI), Demo 4 (asset history trace), and the "affected assets" clause of §8/§26 Workflow B.
7. **Recommended resolution:** Add `domain/20_asset_model.md` defining `Plant`, `Unit`, `Equipment` as real tables with FKs to Organization/Workspace, plus `MaintenanceEvent`, `Inspection`, `Incident` as child entities of Equipment, following the exact field-table format already used by every other `domain/*.md` file.
8. **Difficulty:** Medium — no new infrastructure (per the master prompt's own §7 guidance to avoid a separate graph DB), but touches Document/Evidence schemas to add FK linkage, and needs API/schema/UI follow-through.
9. **Classification: FIX NOW.** This is the root dependency for 4 other gaps (§7, §9's asset-mapping half, §37, §43) — fixing it late means redoing downstream work.

### §7 — Asset-centric industrial knowledge graph

1. **Requirement:** Explicit "Asset-Centric Industrial Knowledge Graph" concept (entities, relationships, provenance, entity resolution, temporal validity), practical PostgreSQL-relational implementation for MVP.
2. **File(s):** repo-wide search
3. **Section/header:** none exists
4. **Why MISSING:** `grep -ril "knowledge graph"`, `"asset-centric"`, `"entity resolution"` across all 680 files → 0 hits, verified directly.
5. **Current status:** 0%.
6. **Affects MVP:** **Yes** — directly named as a §5/§7 differentiator, and feeds Demo 4.
7. **Recommended resolution:** New file `industrial/13_asset_knowledge_graph.md` defining the relationship model (`located_in`, `maintenance_event`, `inspection`, `incident`, `governed_by`, `supersedes`, `maintained_by`) as foreign-key relationships across the §6 entities — explicitly documented as relational (not a new graph DB), per the master prompt's own MVP guidance in §7.
8. **Difficulty:** Medium — mostly a documentation/schema-relationship task once §6 exists; no new runtime component.
9. **Classification: FIX NOW** (immediately after §6, same work session — they're one deliverable split into two files for clarity).

### §9 — Cross-document contradiction detection (independent authoritative sources)

1. **Requirement:** Detect conflicts between two *different, both-authoritative* documents (not two revisions of the same document), surface `CONFLICT DETECTED` with source authority/human-resolution flow.
2. **File(s):** `docs/industrial/06_change_detection.md` (the only file that could plausibly cover this)
3. **Section/header:** "Matching heuristic" section
4. **Why MISSING:** Read in full — the file's entire scope is: *"The specific matching heuristic `05_document_comparison.md` uses to decide whether two findings across documents refer to the 'same' underlying item."* This is revision-diffing (SOP-204 Rev.6 vs. SOP-204 Rev.7 — same lineage). The master prompt's example is SOP-204 vs. an unrelated Maintenance Manual disagreeing at the same point in time — a structurally different problem requiring source-authority comparison, which nothing in the repo does. `grep -ril "contradiction detection"` across the original 680 files (before my own audit files existed) → 0 hits.
5. **Current status:** 0% for independent-source conflicts; the adjacent same-lineage revision-diff capability (§8) is 100% real and could be extended, not reused as-is.
6. **Affects MVP:** **Yes** — explicitly named "core V1" capability in §9, and is Demo 3.
7. **Recommended resolution:** New file `industrial/14_knowledge_conflict_detection.md` implementing the §9 flow: identify sources → compare authority → compare revision → compare effective dates → human review if unresolved. Depends on §37's trust-model fields existing on Document (authority, effective date) to have anything to compare.
8. **Difficulty:** Large — this is genuinely new logic, not a reorganization, and is blocked on §37 first.
9. **Classification: FIX NOW**, but sequenced after §37 (blocking dependency).

### §19 — Safe agent execution trace (explicit, not chain-of-thought)

1. **Requirement:** A defined, safe trace output format (`✓ Retrieved 14 relevant documents...`) distinct from hidden reasoning, with an explicit "never expose chain-of-thought" rule stated.
2. **File(s):** repo-wide search; closest candidate `docs/ui/08_execution_graph_ui.md`
3. **Section/header:** none — `execution_graph_ui.md` was not independently re-verified this pass for content, but the term "execution trace" does not appear anywhere.
4. **Why MISSING:** `grep -ril "execution trace"` → 0 hits across 680 files, verified directly. The execution graph UI screen likely shows *something* (a plan graph), but there is no written spec of the specific safe-trace text format, nor an explicit rule against exposing chain-of-thought.
5. **Current status:** Unknown/likely 0% for the specific trace-format spec; a plan-graph UI concept may exist adjacent to it.
6. **Affects MVP:** **Yes**, but lower-stakes than §6/§7/§9 — this is a presentation/trust feature, not a capability gap.
7. **Recommended resolution:** Add a "Safe execution trace" section to `ui/08_execution_graph_ui.md` or a new `features/04_agent_kernel/16_execution_trace.md`, defining the exact trace-line format and explicitly stating the no-chain-of-thought rule (which should also be added to the §52 principles list once that's rewritten).
8. **Difficulty:** Small.
9. **Classification: DOCUMENT ONLY** — this is a UI/output-format decision, cheap to write, no new backend logic beyond formatting what the agent kernel already tracks.

### §23 — DLP (practical input scanning)

1. **Requirement:** Detect credentials/API keys/secrets/PII/restricted info at input time, with allow/redact/block flow.
2. **File(s):** repo-wide search; closest adjacent file `docs/security/13_secret_exposure.md`
3. **Section/header:** none — no DLP feature group exists among the 26 `features/` groups
4. **Why MISSING:** No feature group named DLP/data-loss-prevention exists. `security/13_secret_exposure.md` (verified by name/context in the threat model table) covers *output* redaction at the logging/response layer — the mitigation column says "Redaction at logging/response layer," which is the opposite end of the pipe from §23's "Input → DLP Scan → allow/redact/block → Agent" flow.
5. **Current status:** 0% for input-side DLP; output-side secret redaction exists as a security control but is a different capability.
6. **Affects MVP:** Ambiguous — §23 says "keep DLP but make it practical," implying it was assumed present in the source material being refactored; it is not present in the current tree at all.
7. **Recommended resolution:** Either add a DLP feature group (new `features/27_dlp/` or fold into `19_identity_and_rbac`/ingestion pipeline) or make an explicit decision to demote it to `later/` — right now it's silently absent, which §54 ("do not invent features," implicitly: do not silently drop them either) flags as needing a documented decision either way.
8. **Difficulty:** Medium if built for real; trivial if formally demoted.
9. **Classification: DOCUMENT ONLY for now** — write a decision-log entry (like DEC-018/019) explicitly scoping DLP out of V1 with a named reason, rather than leaving an undocumented silent gap. Revisit as FIX NOW only if the SIH judging criteria specifically reward it.

### §30 — MUST IMPLEMENT / STUB / OPTIONAL / FUTURE tagging

1. **Requirement:** Every subsystem document explicitly tagged with one of these four implementation-boundary labels.
2. **File(s):** repo-wide — all `docs/features/*/*.md` (≈300 files)
3. **Section/header:** none
4. **Why MISSING:** `grep -rl "MUST IMPLEMENT"` and `grep -rl "STUB"` across all 680 files → 0 hits both, verified directly. The closest existing thing is `reference/10_feature_matrix.md`'s V1-committed/V1-aspirational/V2 labels, which apply at the *feature-group* level (26 groups), not the *individual-file* level §30 asks for.
5. **Current status:** 0% at the file level; ~60% at the group level (feature matrix exists, just coarser granularity and different vocabulary).
6. **Affects MVP:** **Yes** — directly blocks an implementer from knowing what's required per file without reading all 30 sections and inferring.
7. **Recommended resolution:** Add a one-line tag to each feature file's header block (next to the existing "Risk level:" line) once the underlying MUST/STUB/OPTIONAL/FUTURE decision is made per file — mechanical once decided, but the *decision* itself requires product judgment file-by-file.
8. **Difficulty:** Large in aggregate (300 files) even though each edit is trivial — this should be batched, not done file-by-file by hand.
9. **Classification: FIX NOW at the group level** (cheap: extend `reference/10_feature_matrix.md` to the 5-tier vocabulary from §28, which mostly resolves this too) — **DOCUMENT ONLY / defer the per-file tagging** unless implementation is starting immediately, since it's high-volume, low-risk-if-delayed work.

### §31 — Authoritative technology stack document

1. **Requirement:** One document with the exact §31 table (Layer/Technology/MVP Status) for Frontend, Backend, Database, Vector Search, Keyword Search, Agent Runtime, Local Inference, OCR, Auth, Cache/Queue, Sandbox, Reverse Proxy, Observability.
2. **File(s):** `docs/06_TECHNOLOGY_STACK.md`
3. **Section/header:** entire file — "Purpose," "Content" (§1–3), "Related documents," "Maintenance"
4. **Why MISSING:** Read in full (reproduced verbatim in the prior audit). Every section is the generic root-doc template: *"Technology Stack is authoritative for its topic across the entire Sovereign AI Workbench specification..."* — zero technology names, zero table, zero MVP-status column. The real answers exist scattered across 16 files in `docs/integrations/` (`02_vllm.md` through `15_grafana.md`) and `20_DECISION_LOG.md` (DEC-002 through DEC-007), but are never assembled into the one authoritative table this file's entire job is to be.
5. **Current status:** 0% in the file itself; ~80% of the underlying content exists elsewhere, unassembled.
6. **Affects MVP:** **Yes** — explicitly the single most concretely-specified document in the master prompt (§31 includes a literal table to fill in).
7. **Recommended resolution:** Rewrite `06_TECHNOLOGY_STACK.md` with the real table, sourced by cross-referencing each `integrations/*.md` file and the relevant DEC-### entries — this is assembly work, not new design.
8. **Difficulty:** Small — the answers already exist, this is a compilation task.
9. **Classification: FIX NOW** — highest ratio of "master-prompt visibility" to "actual effort" of any item on this list.

### §37 — Knowledge trust model (Source/Authority/Revision/Effective Date/Freshness/Classification/Verification/Conflict/Provenance)

1. **Requirement:** Every knowledge item carries these 9 properties.
2. **File(s):** `docs/domain/13_evidence_model.md`, `docs/domain/06_document_model.md`
3. **Section/header:** both files' "Fields" tables
4. **Why MISSING:** Read in full, both tables. Document has: `id, workspace_id, filename, mime_type, size_bytes, sha256, storage_uri, classification, state, version, uploaded_by, created_at, deleted_at` — no `authority`, no `effective_from`/`effective_until`, no `verification_status`. Evidence has: `id, task_id, source_document_id, document_version, chunk_id, page_number, source_hash, retrieval_method, confidence, created_at` — no `authority`, no `conflict_status`, no `verification_status`. Only 3 of the 9 required properties exist across both entities: Classification ✓, Revision (as bare `version` integer, not a full revision-authority model) ~half-✓, Provenance (via `source_document_id`/`chunk_id` FK chain) ✓.
5. **Current status:** ~33%.
6. **Affects MVP:** **Yes** — this is the single highest-leverage gap; §9, §12, §38, §39 all fail partly or fully because of it.
7. **Recommended resolution:** Add `authority` (enum or FK to a source-authority reference table), `effective_from`/`effective_until` (timestamptz, nullable), and `verification_status`/`conflict_status` (enum) fields to Document and/or Evidence as appropriate, following the existing field-table format.
8. **Difficulty:** Medium — straightforward schema addition, but has ripple effects into API/schema docs (`schemas/07_document_schema.md`, `09_evidence_schema.md`) that must be kept in sync.
9. **Classification: FIX NOW** — root-cause fix for four other gaps.

### §38 — Temporal knowledge (document validity windows)

1. **Requirement:** Documents carry validity ranges so a query like "what was applicable in 2024?" retrieves historically correct information, without mixing current and historical procedures.
2. **File(s):** repo-wide search; `docs/domain/06_document_model.md`
3. **Section/header:** Document "Fields" table
4. **Why MISSING:** Same evidence as §37 — `version` is a bare incrementing integer with no associated date range. `grep -ril "temporal validity"` / `"temporal knowledge"` → 0 hits repo-wide.
5. **Current status:** 0%.
6. **Affects MVP:** **Yes**, though lower urgency than §37/§6 — it's a specific query capability, not a structural blocker for the other gaps.
7. **Recommended resolution:** Same field addition as §37 (`effective_from`/`effective_until`), plus a retrieval-time filter in `features/13_knowledge_fabric/` so a dated query excludes out-of-range document versions — this second part is genuinely new retrieval logic, not just a schema field.
8. **Difficulty:** Medium — schema part is small (bundled with §37); the retrieval-filter part requires touching `13_knowledge_fabric/09_hybrid_search.md`'s actual query logic.
9. **Classification: FIX NOW for the schema fields** (bundle with §37) — **DOCUMENT ONLY / STUB for the retrieval-time filter** unless a demo scenario specifically needs "what was true in 2024" as a live query; otherwise document it as a known-supported-by-schema-but-not-yet-wired-into-retrieval item.

### §39 — Knowledge conflict resolution mechanism

1. **Requirement:** Controlled resolution flow (identify sources → compare authority → compare revision → compare effective dates → human review if unresolved), never silently overwriting one source with another.
2. **File(s):** repo-wide search
3. **Section/header:** none
4. **Why MISSING:** Direct consequence of §37 — there is no `authority` or `effective_date` field to compare, so no resolution logic can exist yet. No file attempts this.
5. **Current status:** 0%.
6. **Affects MVP:** **Yes** — same dependency chain as §9.
7. **Recommended resolution:** This is the same deliverable as §9's contradiction detection — do not build separately; §9's `industrial/14_knowledge_conflict_detection.md` should include this resolution flow as its second half.
8. **Difficulty:** Folded into §9's estimate — no separate cost.
9. **Classification: FIX NOW**, same file/session as §9, sequenced after §37.

### §43 — Industrial asset UI (equipment page)

1. **Requirement:** A screen showing an equipment asset's status/location/manufacturer, maintenance/inspection history, incidents, related SOPs and revisions, known risks, AI insights.
2. **File(s):** `docs/ui/` directory (22 screen files) and `docs/ui/03_navigation.md`
3. **Section/header:** `03_navigation.md`'s "Top-level navigation" and "Task-scoped navigation" tables (both read in full)
4. **Why MISSING:** The full navigation route table lists exactly 8 top-level routes (Workbench, Chat, Documents, Approvals, Security, Network, Models, Admin) and 4 task-scoped routes (Task detail, Execution graph, Evidence, Artifacts) — 12 routes total, none named Assets or Equipment. `grep -rli "asset" docs/ui/` matches only `01_ui_architecture.md`, and in context that's about frontend build assets, not equipment.
5. **Current status:** 0%.
6. **Affects MVP:** **Yes** — named explicitly in §43 as what "turns the system into an industrial intelligence application instead of a chatbot," i.e., core to the whole repositioning goal. Also blocks Demo 4.
7. **Recommended resolution:** New file `ui/23_asset_view.md` with a route (e.g. `/assets/:assetId`) added to `03_navigation.md`'s top-level table. Blocked on §6 (needs an Equipment entity to display).
8. **Difficulty:** Small once §6 exists (this repo's screen-spec files are consistently ~30-40 lines of real content, per `ui/13_network_panel.md`'s pattern) — the difficulty is almost entirely in §6, not here.
9. **Classification: FIX NOW**, sequenced after §6.

### §52 — Architectural Principles document (15 named principles)

1. **Requirement:** The 15 non-negotiable principles from §52 (local-first, evidence before assertion, retrieval before generation, verification after generation, least privilege, human approval for high-risk, retrieved content is untrusted, deterministic components for deterministic calculations, audit every action, respect classification throughout, fail closed, never silently resolve contradictions, never expose unauthorized context, prefer explainable traces over hidden reasoning) stated explicitly, once, as the document everything else defers to.
2. **File(s):** `docs/05_ARCHITECTURAL_PRINCIPLES.md`
3. **Section/header:** entire file
4. **Why MISSING:** Read in full (reproduced verbatim in the prior audit). Identical templated pattern to `06_TECHNOLOGY_STACK.md` — "Purpose... Why this document exists... Content: 1. Statement... 2. Cross-cutting application... 3. Enforcement... Related documents... Maintenance." Zero of the 15 principles appear as text anywhere in the file.
5. **Current status:** 0% — despite this being, per `00_README.md`'s own "Ground rules" section (which is genuine content — "Sovereignty is non-negotiable," "Every action is attributable," "Scope is explicit"), the closest thing to a *partial*, informal version of this document existing somewhere else. But that's 3 rules in a README, not the 15-principle canonical document §52 wants.
6. **Affects MVP:** **Yes** — every other document in the tree is written to defer to this file (per `18_DOCUMENTATION_INDEX.md`'s own stated pattern), so its emptiness is a single point of failure for the tree's internal consistency claim.
7. **Recommended resolution:** Replace the templated body with the 15 principles from §52 verbatim, each with 1–2 sentences grounding it in this specific architecture (e.g., principle 8 "retrieved content is untrusted data" → cite `security/05_prompt_injection.md`; principle 9 "deterministic components for deterministic calculations" → cite `features/07_calculator_tool/05_deterministic_verification.md`).
8. **Difficulty:** Small — this is a writing task drawing on content that mostly already exists elsewhere in the tree; it's an assembly problem like §31, not new design.
9. **Classification: FIX NOW** — tied with §31 for best effort-to-visibility ratio, and structurally more important since other documents are supposed to point to it.

---

## PART 2 — CONTRADICTORY (4 items)

### §12 — Redesign confidence (no fake precision without calibration)

1. **Requirement:** Do not present a bare numeric confidence score as factual probability unless a calibrated methodology is documented; prefer the qualitative Evidence Coverage / Source Authority / Freshness / Cross-Source Agreement / Contradictions / Verification representation.
2. **File(s):** `docs/domain/13_evidence_model.md`, `docs/features/14_evidence_and_provenance/08_confidence.md`
3. **Section/header:** Evidence "Fields" table (`confidence` row); `08_confidence.md` §1 "Purpose"
4. **Why CONTRADICTORY:** `Evidence.confidence` is defined as `real, 0.0–1.0, retrieval/rerank score` — presented as a plain number with no accompanying methodology note, no calibration statement, no limitations disclaimer. This is precisely the pattern §12 opens by prohibiting: *"Do NOT rely on fake precision such as: Confidence = 94% unless there is a clearly defined calibrated methodology."* Worse, `08_confidence.md` — the one file whose entire job is to define this — is the generic template and never once addresses methodology or calibration; its only content is boilerplate API-contract sections (inputs/outputs/error codes) that treat "confidence" as an opaque CRUD resource, not a number requiring justification.
5. **Current status:** The field exists and is wired into Evidence/citations, but its presentation actively violates the explicit instruction rather than merely lacking coverage — hence CONTRADICTORY, not MISSING.
6. **Affects MVP:** **Yes** — evidence/citation is a CORE MVP capability (REQ-FUNC-005), so this number will be user-facing in the demo.
7. **Recommended resolution:** Two valid paths, either is acceptable: (a) replace the single number in UI-facing contexts with the qualitative representation from §12 (Evidence Coverage: High/Source Authority: High/etc.), keeping the raw score as an internal ranking signal only; or (b) keep the number but add a documented methodology (exactly how the 0.0–1.0 score is computed — retrieval similarity? reranker logit? — and its stated limitations) to `08_confidence.md`, replacing its current boilerplate body.
8. **Difficulty:** Small for option (b) — documentation-only, the number and its computation already exist in the retrieval pipeline; Medium for option (a) — requires a UI change in `ui/09_evidence_panel.md` too.
9. **Classification: FIX NOW** — this is the master prompt's most explicit, most specific prohibition ("Confidence = 94%" is its literal example), so leaving it as-is is the highest-visibility inconsistency in the whole tree if a judge or reviewer reads both documents side by side.

### §27 — Demote generic features (don't let them be primary differentiators)

1. **Requirement:** Generic coding agent / spreadsheet agent / chatbot / memory / calculator / multimodal stay as supporting platform capabilities; the primary product story stays industrial intelligence.
2. **File(s):** `docs/demo/06_coding_agent_demo.md`, `docs/demo/08_spreadsheet_demo.md`, `docs/reference/10_feature_matrix.md`
3. **Section/header:** `demo/` directory listing (file-level, all 15 files); `reference/10_feature_matrix.md` row "Spreadsheet Intelligence (23)"
4. **Why CONTRADICTORY:** The feature matrix *does* correctly demote spreadsheet intelligence in writing: *"Supporting workflow, not the primary demo path."* But the `demo/` directory's actual file structure contradicts that written intent — `06_coding_agent_demo.md` and `08_spreadsheet_demo.md` sit as numbered peers alongside `05_inspection_report_demo.md`, `10_evidence_demo.md`, `11_approval_demo.md`, `12_sovereignty_demo.md` — i.e., structurally equal-weighted with the flagship industrial demos. Meanwhile, document-revision-comparison and contradiction-detection — the capabilities §26 explicitly calls "flagship" — have **no dedicated demo file at all** among the 15. The directory structure says the opposite of what the feature matrix and master prompt say.
5. **Current status:** Written policy (feature matrix) says one thing; structural artifact (demo directory) does the other.
6. **Affects MVP:** **Yes** — directly shapes what the SIH demo actually walks through.
7. **Recommended resolution:** Add `demo/16_sop_revision_demo.md` and `demo/17_contradiction_demo.md` (the latter blocked on §9 existing as a feature first). Consider renumbering `06_coding_agent_demo.md`/`08_spreadsheet_demo.md` into a clearly-labeled "supporting capabilities" appendix rather than the main sequential list, so the file structure matches the stated intent.
8. **Difficulty:** Small for the renumbering/labeling; the two new demo files are Medium-to-Large since one (contradiction demo) can't be written meaningfully until §9 has a real feature behind it.
9. **Classification: DOCUMENT ONLY for the renumbering** (cheap, immediate, resolves the contradiction as written policy vs. structure) — **FIX NOW is blocked** for the contradiction-demo file specifically until §9 ships; write it as a placeholder/FUTURE marker in the interim rather than leaving the gap silent.

### §33 — Reduce documentation duplication via canonical references

1. **Requirement:** Feature documents should reference canonical rules documents (security requirements, audit requirements, error handling, API conventions, etc.) rather than repeating the same ~20 sections in every file.
2. **File(s):** all `docs/features/*/*.md` (≈300 files) — sampled directly: `features/21_policy_engine/05_model_policies.md`, `features/16_human_approval/02_action_risk_classification.md`, `features/09_code_execution/09_execution_timeout.md`, `features/14_evidence_and_provenance/08_confidence.md`, `features/18_network_sovereignty/12_sovereignty_status.md`
3. **Section/header:** all 30 numbered sections in each file, specifically sections 15 (Security requirements), 18 (Retry behavior), 21 (Observability requirements), 22 (Audit requirements) — verified identical boilerplate structure across all 5 sampled files from 5 different feature groups
4. **Why CONTRADICTORY:** This is the literal opposite of what §33 asks for. Instead of each file referencing one canonical security/audit/retry doc and only writing its own specific 3–5 sections, every one of ~300 files repeats the full skeleton with near-identical prose (e.g. section 18 in every sampled file: *"This feature's calls are classified `interactive-read` operations... defined once, canonically, in `docs/runtime/11_retry_policy.md` — this file does not restate those numbers"* — the file states it isn't restating the numbers, immediately after restating the same three sentences of framing around that fact, in all 300 files). The repetition itself is the violation, independent of whether the underlying canonical doc (`11_retry_policy.md`) exists and is good — it does exist and likely is fine; the boilerplate wrapper repeated 300 times is the problem.
5. **Current status:** Structurally the opposite of the target state — canonical docs exist (`13_DEVELOPER_RULES.md`, `runtime/11_retry_policy.md`, `reference/*`) but aren't leveraged to shrink the per-file repetition; they're referenced *in addition to*, not *instead of*, restating the framework each time.
6. **Affects MVP:** Indirectly — doesn't block any single capability, but is the largest source of "looks complete, isn't" risk (see §58) and the biggest maintenance burden if requirements change.
7. **Recommended resolution:** Define a per-feature-file template with only: Purpose (feature-specific 1-2 sentences), Scope/Non-goals (feature-specific), User-facing behavior, System behavior, Inputs/Outputs (feature-specific), and a single "Governed by: security/audit/retry/observability — see canonical docs" line replacing sections 15/18/21/22/etc. wholesale.
8. **Difficulty:** Large — mechanical per-file once the template is fixed, but 300 files is 300 files; best done as a scripted transformation, not hand-editing.
9. **Classification: DOCUMENT ONLY now** (write the new template, prove it on 2-3 files as an approved pattern) — **FUTURE for the full 300-file rollout**, since it's a real improvement but not something that blocks the SIH demo or MVP functionality; the current repetition is verbose but not incorrect.

### §60 — Final deliverables (superseded conclusion)

1. **Requirement:** An honest final report of what changed, what's still wrong, and remaining risks, per §60(A–H).
2. **File(s):** `docs/22_REFACTOR_AUDIT_REPORT.md` (my own prior output)
3. **Section/header:** §B "Architecture changes" — specifically the line *"No rewrite was needed... the tree already reads as a coherent industrial-intelligence platform, not a generic chatbot."*
4. **Why CONTRADICTORY:** That prior conclusion is now directly contradicted by this document's own findings (§6, §7, §9, §12, §31, §37, §38, §43, §52 above) — the tree does *not* yet function as an asset-centric industrial intelligence platform at the structural level; it's a strong generic-platform spec with an industrial *document-type* layer on top, not an industrial *entity/knowledge-graph* layer.
5. **Current status:** Formally still present in the tree as written, now known to be inaccurate.
6. **Affects MVP:** No direct effect (it's a report, not a capability), but leaving it uncorrected risks someone reading only that file and believing the earlier, wrong conclusion.
7. **Recommended resolution:** Add a superseding note at the top of `22_REFACTOR_AUDIT_REPORT.md` pointing to this document and the summary compliance matrix as the current state of record — do not delete the old report (it's still accurate for the identifier-fix work it actually covered), just correct its scope claim.
8. **Difficulty:** Trivial — a few sentences.
9. **Classification: DOCUMENT ONLY** — but should happen in the same pass as any other edit, so nobody reads stale conclusions in the meantime. *(Not modified yet, per your instruction to hold all changes.)*

---

## PART 3 — PARTIAL (27 items)

### §4 — Positioning language (industrial intelligence, not generic agentic workbench)
1. **File(s):** `docs/00_README.md` § opening paragraph; `docs/01_PRODUCT_VISION.md`
2. **Why PARTIAL:** README's actual first sentence: *"a locally-hosted, sovereignty-first AI workbench that plans and executes multi-step agentic tasks — document Q&A, spreadsheet analysis, coding, report generation."* This is close kin to §4's explicitly-banned "generic multi-agent platform" framing — industrial intelligence isn't mentioned until later, if at all in this file (not fully re-verified past the opening paragraph this pass). No banned exact phrases ("Local ChatGPT" etc.) appear, so it's not a full violation, just a mis-ordered emphasis.
3. **MVP-affecting:** Yes — first impression for judges reading the README.
4. **Resolution:** Rewrite opening 1-2 sentences to lead with the §62 framing.
5. **Difficulty:** Small. **Classification: FIX NOW.**

### §5 — Product hierarchy diagram (Platform → Industrial Intelligence + Sovereign AI Core)
1. **File(s):** `docs/04_SYSTEM_ARCHITECTURE.md` § "High-level shape"
2. **Why PARTIAL:** Read in full — defines 5 layers (UI/API/Agent kernel/Capability/Trust). Industrial intelligence is not one of the 5 layers, nor mentioned anywhere in this file at all (confirmed by direct read) — it's absent from the system's own top-level self-description, not just under-diagrammed.
3. **MVP-affecting:** Yes.
4. **Resolution:** Add industrial intelligence as an explicit 6th consideration or sub-layer of Capability, with the §5 two-branch diagram.
5. **Difficulty:** Small (once §6/§7 exist to describe). **Classification: FIX NOW**, sequenced after §6/§7.

### §10 — Evidence chain (6-hop: Source→Version→Page/Section→Chunk→Claim→Answer)
1. **File(s):** `docs/domain/13_evidence_model.md` § "Fields"
2. **Why PARTIAL:** 4 of 6 hops present as real FKs (`source_document_id`, `document_version`, `chunk_id`, `page_number`); "Section" and explicit "source timestamp/metadata" are not fields.
3. **MVP-affecting:** Small effect — mostly complete already.
4. **Resolution:** Add `section_reference` field.
5. **Difficulty:** Small. **Classification: FIX NOW** (bundle with §37 schema work).

### §11 — Explicit verification pipeline (8 named checks as one flow)
1. **File(s):** `docs/features/14_evidence_and_provenance/09_unsupported_claim_detection.md`
2. **Why PARTIAL:** File is the generic template (pattern confirmed across the group); defines unsupported-claim detection in isolation, not the 8-branch pipeline as one named flow.
3. **MVP-affecting:** Yes.
4. **Resolution:** New file wiring the 8 checks (citation validity/evidence support/contradiction/unsupported claims/source authority/freshness/policy/classification) as one pipeline.
5. **Difficulty:** Medium — some checks (contradiction, source authority) don't exist yet (§9, §37), so this file can only be completed after those. **Classification: DOCUMENT ONLY now** (write the pipeline skeleton with TBD markers per §54 for the not-yet-real checks) — **FIX NOW fully** once §9/§37 land.

### §13 — Risk-aware model router (9 named inputs)
1. **File(s):** `docs/features/02_model_router/*` (10 files: overview, capability_matching, task_classification, model_scoring, resource_fit, policy_fit, accuracy_fit, latency_fit, fallback_routing, multi_model_routing)
2. **Why PARTIAL:** File *names* map almost 1:1 onto §13's input categories, but bodies are the generic template (verified in 2 of 10 directly, e.g. `01_router_overview.md`/`02_capability_matching.md` follow the identical "X is the unit of Model Router responsible for... as it specifically relates to 'x'" pattern) — actual scoring/weighting formula for how policy_fit + accuracy_fit + latency_fit combine into one routing decision isn't written anywhere.
3. **MVP-affecting:** Yes — core routing behavior.
4. **Resolution:** Write the actual combination logic once, likely in `01_router_overview.md`, replacing its templated body.
5. **Difficulty:** Medium. **Classification: FIX NOW** for the overview file; the 9 sub-files' templated bodies can follow the §33 remediation later.

### §15 — Context security boundary (explicit named 7-hop chain)
1. **File(s):** `docs/architecture/09_trust_boundaries.md`, `10_privilege_boundaries.md`, `features/13_knowledge_fabric/12_permission_filtering.md`
2. **Why PARTIAL:** The substance (identity→permissions→document access→evidence→tools→models→artifacts→exports) is scattered correctly across `19_identity_and_rbac/`, `20_data_classification/`, `13_knowledge_fabric/12_permission_filtering.md` — but no single document names and diagrams the full chain as one concept called "Context Security Boundary."
3. **MVP-affecting:** Yes — this is exactly the "don't treat UI-level RBAC as sufficient" point §15 makes, and it's currently implicit rather than an explicit, checkable architectural invariant.
4. **Resolution:** Add one document (or a section in `architecture/09_trust_boundaries.md`) explicitly naming and diagramming the 7-hop chain, cross-referencing the files where each hop is actually enforced.
5. **Difficulty:** Small — assembly of already-correct pieces. **Classification: FIX NOW.**

### §17 — Human-in-the-loop governance (4-tier LOW/MEDIUM/HIGH/CRITICAL)
1. **File(s):** `docs/reference/03_risk_levels.md`
2. **Why PARTIAL:** Read in full — real, concrete, well-reasoned 3-tier table (low/medium/high) with a genuinely good escalation rule (risk = f(action, classification)). But only 3 tiers, not 4; nothing separates "modify database" (should arguably be HIGH) from "execute operational command" (should arguably be CRITICAL) — both currently fall under `high`.
3. **MVP-affecting:** Small-to-moderate — the 3-tier system may be sufficient for V1's actual action set, but the master prompt's explicit example ("execute operational cmd -> CRITICAL") implies a 4th tier matters for anything approaching real industrial control actions.
4. **Resolution:** Either add a `critical` tier for irreversible-and-high-consequence actions, or add one sentence to `03_risk_levels.md` explicitly justifying why 3 tiers is a deliberate, sufficient simplification for this system's actual action set (V1 has no direct operational-control actions, so CRITICAL may genuinely be unneeded — but this should be a stated decision, not silent).
5. **Difficulty:** Small either way. **Classification: DOCUMENT ONLY** (write the justification, or add the 4th tier — either resolves the gap cheaply).

### §20 — Sovereignty attestation (runtime verification mechanism)
1. **File(s):** `docs/features/18_network_sovereignty/12_sovereignty_status.md`, `docs/ui/13_network_panel.md`
2. **Why PARTIAL:** `ui/13_network_panel.md` (read in full) is genuinely specific: blocked-checks list, blocked-attempts counter, a distinct error state for "monitor unreachable" vs. "checks currently passing" — closer to real runtime verification than a bare UI claim. But `12_sovereignty_status.md`, the backend feature that would actually *produce* that attestation, is the generic template — the mechanism (what process runs the checks, how often, what "PASSED" means mechanically) isn't specified anywhere.
3. **MVP-affecting:** Yes — this is a named core demo beat (Demo 8).
4. **Resolution:** Write the actual attestation mechanism into `12_sovereignty_status.md`, replacing its templated body.
5. **Difficulty:** Small-Medium. **Classification: FIX NOW.**

### §22 — Auditability (hash chain construction + independent verify/export)
1. **File(s):** `docs/features/17_audit/10_audit_integrity.md`, `docs/domain/17_audit_event_model.md`, `docs/schemas/15_audit_event_schema.md`
2. **Why PARTIAL:** Hash-chain concept is referenced consistently elsewhere (threat model: *"DB-level append-only grant + hash chain"*), but `10_audit_integrity.md` itself is the generic template — the actual chain construction (does the schema have `prev_hash`/`hash` fields? what's the verify-on-export procedure?) was not confirmed present in `schemas/15_audit_event_schema.md` this pass.
3. **MVP-affecting:** Yes — audit integrity is a CORE MVP, demo-critical capability (Demo/audit trail beat).
4. **Resolution:** Verify (read) `schemas/15_audit_event_schema.md` directly for `prev_hash`/`hash` fields; if absent, add them; write the real verify-export procedure into `10_audit_integrity.md`.
5. **Difficulty:** Small if fields already exist (verification only); Medium if they need adding. **Classification: FIX NOW** (verification is cheap and this is demo-critical — worth confirming before assuming either way).

### §24 — Sandboxing (10 named controls)
1. **File(s):** `docs/features/09_code_execution/*` (14 files)
2. **Why PARTIAL:** All 10 §24 bullets have a corresponding file by name (container_creation, resource_limits, network_isolation, process_isolation, filesystem_isolation, execution_timeout, etc.) — but bodies are templated (verified directly in `09_execution_timeout.md`). Actual limit values (CPU/memory caps, timeout seconds) are asserted to live in `performance/03-06_*_budgets.md` via cross-reference, not independently confirmed present there this pass.
3. **MVP-affecting:** Yes — security-critical (Demo/sandbox-escape test).
4. **Resolution:** Confirm each `09_code_execution/*` file's cross-reference actually resolves to a real number in `performance/`, not a placeholder.
5. **Difficulty:** Small (verification pass). **Classification: FIX NOW** (cheap to check, high consequence if numbers are missing).

### §28 — 5-tier feature priority system
1. **File(s):** `docs/reference/10_feature_matrix.md`
2. **Why PARTIAL:** Real, concrete matrix — but uses its own 3-value vocabulary (V1-committed / V1-aspirational / V2), not §28's CORE MVP/V1/V1.5/FUTURE/RESEARCH. `grep` for "CORE MVP," "V1.5," "RESEARCH" → 0 hits.
3. **MVP-affecting:** Yes — same document also needed for §30/§57.
4. **Resolution:** Remap the 3 existing values onto the 5-tier vocabulary (V1-committed → CORE MVP or V1 depending on demo-criticality; V1-aspirational → V1.5; V2 → FUTURE), or explicitly justify the simplified 3-tier system.
5. **Difficulty:** Small. **Classification: FIX NOW** — this single edit also substantially resolves §30 and improves §57.

### §29 — Reduced 16-item MVP list
1. **File(s):** `docs/08_BUILD_PHASES.md`, `docs/reference/10_feature_matrix.md`
2. **Why PARTIAL:** `08_BUILD_PHASES.md` (read in full) is genuinely excellent — real 11-phase (0–10) roadmap with concrete exit criteria per phase, not templated. But its V1-committed scope (per the feature matrix) is broader than §29's 16-item list: it includes admin console, observability, backup/recovery, agent memory as V1-committed, none of which appear in §29's list.
3. **MVP-affecting:** Yes — this is exactly the scope-bloat risk §29 exists to prevent.
4. **Resolution:** Either explicitly justify each addition beyond §29's 16 items (admin console/observability/backup arguably needed for *any* deployable system, which is a defensible reason — but it should be stated), or trim scope.
5. **Difficulty:** Small (a documentation/decision-log entry). **Classification: DOCUMENT ONLY** — the existing 11-phase plan is strong; this just needs an explicit reconciliation note against §29, not a rewrite.

### §34 — Single source of truth (master architecture document, 13-item checklist)
1. **File(s):** `docs/04_SYSTEM_ARCHITECTURE.md`
2. **Why PARTIAL:** Read in full. Covers: architecture ✓, system boundaries ✓ (via layers), major components ✓, data flow ✓, security boundaries ✓ (trust layer), deployment model ✓ (links to 4 deployment-mode docs). Does NOT explicitly cover: product vision (lives in `01_PRODUCT_VISION.md` instead — arguably fine, cross-referenced), sovereignty model (implied, not named as its own item), agent model (implied via layer 3, not detailed), evidence model (not mentioned at all in this file), **industrial intelligence model (completely absent — confirmed, see §5 above)**, MVP scope (not in this file — lives in `08_BUILD_PHASES.md`/feature matrix instead).
3. **MVP-affecting:** Yes.
4. **Resolution:** Either add the missing items directly to this file, or add a "coverage map" section explicitly stating which of the 13 §34 items live in which other file (since the master prompt itself allows a single *logical* source of truth spread with clear pointers, not necessarily one physical file) — the current gap is that this mapping isn't stated, so a reader can't tell if evidence model and industrial intelligence model were forgotten or deliberately live elsewhere.
5. **Difficulty:** Small (a section explaining the mapping) to Medium (if content should be inlined). **Classification: DOCUMENT ONLY** — add the coverage-map section first; only inline content that's still genuinely missing (industrial intelligence model, once §6/§7 exist).

### §36 — Threat model (6-column table + 5 missing named threats)
1. **File(s):** `docs/security/02_threat_model.md`
2. **Why PARTIAL:** Read in full. Real, concrete 20-row table — but only has Threat/File/Severity/Mitigation columns (4 of §36's 6: Threat, Impact, Likelihood, Mitigation, Residual Risk, Test — missing Likelihood and Residual Risk and Test at the index level; these may exist in the 20 per-threat detail files, not independently verified this pass). Also missing 5 of §36's 15 named threat categories from the index: compromised local user, unauthorized model access, malicious generated artifacts, poisoned knowledge, stale documents.
3. **MVP-affecting:** Yes — security-critical, demo-adjacent (RBAC-denial and sandbox-escape beats reference this model).
4. **Resolution:** Add Likelihood/Residual Risk columns to the index (or confirm + link them from per-threat files); add rows for the 5 missing threats — "poisoned knowledge" and "stale documents" are especially relevant given the §37/§38 gaps above.
5. **Difficulty:** Small (index table edit) + Medium (5 new per-threat detail files if going deep, or Small if index-only rows suffice for V1). **Classification: FIX NOW for the index table** (cheap); **DOCUMENT ONLY / FUTURE for full per-threat detail files** on the 5 new entries unless SIH judging specifically probes security depth.

### §40 — UI reflects the product (11 named areas)
1. **File(s):** `docs/ui/03_navigation.md`
2. **Why PARTIAL:** Read in full. Nav table has 8 top-level + 4 task-scoped = 12 routes covering: Documents (~Knowledge) ✓, Approvals ✓, Security ✓, Network (~sovereignty, not exactly "System Status") ✓, Models ✓, Admin ✓. Missing explicit: **Assets** (see §43), **Workflows**, **Reports** (report generation exists as a workflow but has no dedicated browsable screen/route), **Agents** (agent runs aren't independently browsable outside a task context), **Dashboard** (closest is "Workbench" — a naming variance, arguably fine).
3. **MVP-affecting:** Yes.
4. **Resolution:** Add Assets (blocked on §6/§43), Workflows, and Reports as top-level nav entries; consider whether standalone Agents browsing is needed for V1 or is adequately covered by task-scoped agent state.
5. **Difficulty:** Small per route once underlying data model exists; Assets is blocked on §6. **Classification: FIX NOW for Workflows/Reports routes** (no blocking dependency) — **sequenced after §6 for Assets.**

### §41 — Sovereignty status UI (exact field vocabulary)
1. **File(s):** `docs/ui/13_network_panel.md` § "Key elements"
2. **Why PARTIAL:** Real screen spec (blocked-checks list, blocked-attempts counter) but doesn't use §41's specific field set (Mode/Internet/External AI/Local Models/Local Knowledge/Network Attestation) — a vocabulary/presentation gap, not a missing capability.
3. **MVP-affecting:** Small — cosmetic relative to other gaps, though visually this is the "core visual differentiator" §41 calls it, so worth getting the labeling right for the demo.
4. **Resolution:** Align "Key elements" list to the exact §41 field names.
5. **Difficulty:** Trivial. **Classification: FIX NOW** — cheapest item on this entire list.

### §42 — Evidence UI (Answer→Evidence→Document/Revision/Page/Section, Verification, Conflicts, Actions)
1. **File(s):** `docs/ui/09_evidence_panel.md` (not independently re-verified in full this pass — flagging honestly)
2. **Why PARTIAL:** File exists in the real (non-templated) screen-spec tier based on its sibling files' pattern, but given Evidence's missing "section" field (§10) and missing conflict-status field (§37), the UI *cannot* fully expose a "Conflicts" sub-panel even if the screen spec otherwise covers Document/Revision/Page/Verification/Actions.
3. **MVP-affecting:** Yes — demo-critical (citation-inspection beat).
4. **Resolution:** Direct-read this file against the 5-item checklist; the Conflicts sub-panel is blocked on §37 regardless of what this file currently says.
5. **Difficulty:** Small (verification) + dependent on §37 for the Conflicts piece. **Classification: DOCUMENT ONLY now** (verify current content) — **FIX NOW for Conflicts sub-panel** once §37 lands.

### §44 — Report generation as first-class output (11 named sections)
1. **File(s):** `docs/workflows/07_report_generation.md`
2. **Why PARTIAL (bordering MISSING):** Read in full — the entire file is 3 steps: (1) compile findings into DOCX, (2) compute classification as max of cited evidence, (3) require approval if ≥CONFIDENTIAL. Of §44's 11 required report sections (executive summary, findings, evidence, source references, affected assets, detected conflicts, changes, calculations, recommendations, uncertainty, approval state), only "approval state" (step 3) and implicitly "evidence/source references" (via step 1's citations) are covered — roughly 2–3 of 11.
3. **MVP-affecting:** Yes — Demo 5 depends on this.
4. **Resolution:** Expand this file into the full 11-section report structure; "affected assets" and "detected conflicts" sections are blocked on §6/§9 respectively, so those two sub-sections should be marked TBD/FUTURE within the file rather than blocking the rest.
5. **Difficulty:** Medium. **Classification: FIX NOW for the 6–7 sections that don't depend on other gaps** (executive summary, findings, evidence, source references, changes, recommendations, uncertainty) — **FUTURE for affected-assets/detected-conflicts sub-sections** until §6/§9 exist.

### §45 — Safe export controls (concrete check sequence)
1. **File(s):** `docs/features/20_data_classification/11_export_restrictions.md`
2. **Why PARTIAL:** File exists in the classification group but is template-tier (pattern consistent with every other sampled feature file) — the specific 5-step check sequence (permissions→classification→destination→policy→approval) isn't written as one concrete flow, just implied by section headers.
3. **MVP-affecting:** Yes.
4. **Resolution:** Write the concrete check sequence, replacing the templated body.
5. **Difficulty:** Small — this doesn't depend on any other gap; all 5 checks' underlying systems (RBAC, classification, network policy, policy engine, approval) already exist and are real. **Classification: FIX NOW.**

### §49 — Realistic 7-phase roadmap
1. **File(s):** `docs/08_BUILD_PHASES.md`
2. **Why PARTIAL:** Read in full — genuinely strong, real 11-phase (0–10) roadmap with concrete exit criteria, not templated. But structured differently from §49's 7 phases, and — more substantively — **has no phase dedicated to Industrial Intelligence** (§49's Phase 3: asset model, equipment entities, document revisions, contradiction detection, temporal knowledge) or **Industrial Workflows** (§49's Phase 5: inspection intelligence, SOP impact analysis, engineering decision support) as distinct, tracked phases. Document revisions get folded into Phase 6 ("Evidence/provenance") implicitly; nothing tracks §6/§7/§9's new work as a phase with its own exit criteria.
3. **MVP-affecting:** Yes — if these gaps get fixed per this report, there's currently no phase/exit-criterion in the build plan to track that work landing.
4. **Resolution:** Insert an explicit "Phase 5.5 — Industrial Intelligence" (or renumber) between the existing phases, with exit criteria tied to §6/§7/§9's new files/fields actually existing and passing a new acceptance test.
5. **Difficulty:** Small (planning-document edit). **Classification: FIX NOW** — cheap, and needed to make the rest of this remediation plan trackable within the existing process.

### §50 — Demo-first spec (8 named demos)
1. **File(s):** `docs/demo/*` (15 files), primarily `01_demo_overview.md`
2. **Why PARTIAL:** Read `01_demo_overview.md` in full — Demo 1 (evidence-backed Q&A), Demo 6 (unauthorized access/RBAC denial), Demo 7 (approval gate), Demo 8 (air-gap disconnect) are all present and genuinely detailed with concrete UI/data steps (not templated — this file is real content, confirmed). Demo 2 (SOP revision compare) and Demo 3 (contradiction detection) have no dedicated file (Demo 3 is currently impossible — feature doesn't exist, §9). Demo 4 (asset history trace) has no file (blocked on §6/§43). Demo 5 (report generation) exists as a workflow but wasn't independently confirmed as a *demo script* this pass.
3. **MVP-affecting:** Yes — directly the SIH judging artifact.
4. **Resolution:** See §26/§27 above — same underlying gap.
5. **Difficulty:** Small for Demo 2/5 (features exist, just need demo scripting); blocked/Large for Demo 3/4 (features don't exist yet). **Classification: FIX NOW for Demo 2 and Demo 5 scripts** — **FUTURE for Demo 3/4** until §6/§7/§9/§43 land, and the demo narrative should be honest about this in the interim (per your earlier framing option to "narrow the demo script to what's genuinely ready").

### §51 — End-to-end acceptance tests (9 named)
1. **File(s):** `docs/reference/13_test_matrix.md`, `docs/testing/*`
2. **Why PARTIAL:** `13_test_matrix.md` read in full — real, concrete, 10 test-ID groups cross-linked to requirements (TEST-NET-*, SEC-TEST-*, TEST-E2E-*, TEST-APPROVAL-001, TEST-ROUTER-*, TEST-OCR-001, TEST-EVIDENCE-001, TEST-CLASS-001, TEST-AUDIT-*, TEST-PERF-001) — genuinely good coverage for what exists. But no test ID exists for revision-comparison (§8, even though the *feature* is complete) or contradiction-detection (§9, feature doesn't exist so no test is possible yet) — 2 of §51's 9 named test categories have no corresponding entry.
3. **MVP-affecting:** Yes — §8 (revision comparison) is a complete, real feature with no acceptance test tracked, which is an easy, low-risk fix.
4. **Resolution:** Add `TEST-REVISION-001` to the matrix for the already-complete §8 capability now; add `TEST-CONTRADICTION-001` once §9 exists.
5. **Difficulty:** Trivial for the revision test (feature already works, just needs a tracked test ID); blocked for contradiction test. **Classification: FIX NOW for TEST-REVISION-001** — **FUTURE for TEST-CONTRADICTION-001.**

### §53 — Glossary (19 named terms, 4 missing)
1. **File(s):** `docs/19_GLOSSARY.md`
2. **Why PARTIAL:** Read in full — genuinely well-written, 26 real term definitions, each cross-referenced to its owning file. Missing 4 of §53's 19 explicitly-named terms as standalone entries: **Claim**, **Asset**, **Revision**, **Verification** (concepts exist in filenames/prose but have no glossary row); **Reranking** also absent as its own entry despite `13_knowledge_fabric/10_reranking.md` existing.
3. **MVP-affecting:** Low-moderate — a documentation-quality item, not a functional gap.
4. **Resolution:** Add the 5 missing rows. "Asset" definition is blocked on §6 existing to define against; the other 4 can be added immediately.
5. **Difficulty:** Trivial. **Classification: FIX NOW for Claim/Revision/Verification/Reranking** — **sequenced after §6 for Asset.**

### §56 — Documentation structure reorganization
1. **File(s):** current `docs/` tree structure vs. §56's proposed `00-overview/`...`12-sih/` tree
2. **Why PARTIAL:** Current tree uses a different, arguably more granular scheme (root `00`–`22` + 20 topic subdirectories, ~680 files) vs. §56's dozen-directory proposal. The master prompt itself says *"Adapt this structure to the existing repository rather than forcing it mechanically"* — so a literal renumber is explicitly optional per the master prompt's own text, not a compliance failure.
3. **MVP-affecting:** No.
4. **Resolution:** None required; if desired for cosmetic/pitch-deck-narrative reasons, a mapping table (which existing directory = which §56 proposed directory) could be added to `18_DOCUMENTATION_INDEX.md`, but this is optional.
5. **Difficulty:** N/A. **Classification: FUTURE / not needed** — lowest-priority item on this entire list by the master prompt's own permission to skip it.

### §57 — Master feature matrix (exact 6-column format)
1. **File(s):** `docs/reference/10_feature_matrix.md`
2. **Why PARTIAL:** Real table exists (see §28) but groups multiple feature numbers per row ("01-09... Core platform") rather than one row per capability with the 6 named columns (Capability/Priority/MVP/Industrial Value/Security Impact/Demo).
3. **MVP-affecting:** Moderate — the coarse grouping makes it hard to spot which *individual* capabilities are demo-critical vs. supporting.
4. **Resolution:** Expand to one row per feature group (26 rows) with the exact 6 columns; this is largely a reformat of information that already exists in `reference/03_risk_levels.md` (Security Impact ~ Risk level) and the feature matrix's own current Notes column.
5. **Difficulty:** Small-Medium. **Classification: FIX NOW** — bundle with §28's remediation since it's the same file.

### §58 — 13-question quality bar per document
1. **File(s):** all `docs/features/*/*.md` (sampled 5 across different groups)
2. **Why PARTIAL/CONTRADICTORY-adjacent:** Every sampled file formally *has* a section for most of the 13 questions (Purpose/Inputs/Outputs/Dependencies/Trust boundaries/Data access/Permissions/Failure behavior/Audit/Test requirements/MVP status/Industrial contribution) — but answers them with placeholder-shaped prose rather than substance, e.g. "Non-goals" sections consistently say only *"anything owned by a sibling file... and anything listed under Non-goals below"* (self-referential, content-free). This is the same root cause as §33, viewed from the "is each answer actually useful" angle rather than the "is it duplicated" angle.
3. **MVP-affecting:** Indirect — same as §33.
4. **Resolution:** Same as §33's remediation — this is one underlying problem, not two.
5. **Difficulty:** Large (folded into §33). **Classification: DOCUMENT ONLY / FUTURE**, same reasoning and same fix as §33 — do not duplicate effort by treating these as separate remediation items.

### §62 — Final product definition (one coherent idea, stated in the README)
1. **File(s):** `docs/00_README.md`
2. **Why PARTIAL:** Same finding as §4 — the README's actual opening framing doesn't yet state the §62 three-paragraph definition (sovereign industrial intelligence platform / runs AI locally, connects documents to assets, detects contradictions, verifies claims, executes bounded workflows / defining characteristic is organizational control, not just locality). This is the same fix as §4, not a separate one.
2. **MVP-affecting:** Yes.
3. **Resolution:** Same edit as §4 — do not duplicate effort.
4. **Difficulty:** Small. **Classification: FIX NOW**, bundled with §4.

---

## PART 4 — Prioritized Remediation Plan

### P0 — Critical architectural contradictions
*Fix first: these are either explicit prohibitions being violated right now, or single points of failure that every other document is supposed to defer to.*

| # | Item | Classification |
|---|---|---|
| 1 | §52 — Rewrite Architectural Principles (currently empty, everything defers to it) | FIX NOW |
| 2 | §12 — Confidence score contradicts the master prompt's explicit "no fake precision" rule | FIX NOW |
| 3 | §31 — Rewrite Technology Stack doc (currently empty, answer exists elsewhere unassembled) | FIX NOW |
| 4 | §60 — Correct the prior audit report's superseded conclusion | DOCUMENT ONLY |

### P1 — Core industrial differentiation
*The master prompt's central ask. Sequenced: §6 unblocks §7/§9/§37(partially)/§43; §37 unblocks §9/§38/§39.*

| # | Item | Classification | Blocked by |
|---|---|---|---|
| 5 | §6 — Asset/equipment domain entity model | FIX NOW | — |
| 6 | §37 — Knowledge trust model fields (authority, effective date, verification/conflict status) | FIX NOW | — |
| 7 | §7 — Asset-centric knowledge graph relationships | FIX NOW | §6 |
| 8 | §9 + §39 — Cross-document contradiction detection & resolution flow | FIX NOW | §37 |
| 9 | §38 — Temporal knowledge schema fields | FIX NOW | (bundle with §37) |
| 10 | §38 — Temporal retrieval filter (query "what was true in 2024") | DOCUMENT ONLY / STUB | §38 schema |
| 11 | §43 — Industrial asset UI screen | FIX NOW | §6 |
| 12 | §5 / §34 — Add industrial intelligence to system architecture's top-level shape | FIX NOW | §6, §7 |
| 13 | §10 — Add "section" field to Evidence chain | FIX NOW | (bundle with §37) |
| 14 | §44 — Expand report generation to full 11-section structure (minus asset/conflict subsections) | FIX NOW | — |
| 15 | §44 — Affected-assets / detected-conflicts report subsections | FUTURE | §6, §9 |
| 16 | §53 — Add "Asset" glossary term | FIX NOW | §6 |

### P2 — Security / sovereignty / governance
*High-consequence if wrong, but not blocked on new architecture — mostly verification and assembly work.*

| # | Item | Classification |
|---|---|---|
| 17 | §22 — Verify/add audit hash-chain fields in schema; write real integrity-verify procedure | FIX NOW |
| 18 | §24 — Verify sandbox limit values actually resolve in `performance/` budgets | FIX NOW |
| 19 | §20 — Write real sovereignty attestation mechanism (replace template) | FIX NOW |
| 20 | §41 — Align sovereignty status UI field labels to exact spec vocabulary | FIX NOW |
| 21 | §45 — Write concrete export-check sequence (replace template) | FIX NOW |
| 22 | §15 — Name and diagram the Context Security Boundary explicitly | FIX NOW |
| 23 | §17 — Decide 4-tier vs. justify 3-tier risk model | DOCUMENT ONLY |
| 24 | §36 — Add Likelihood/Residual Risk columns + 5 missing threat entries to index | FIX NOW (index) / FUTURE (full detail files) |
| 25 | §23 — DLP: formally scope out of V1 with a decision-log entry, or build | DOCUMENT ONLY |
| 26 | §19 — Write safe execution trace format spec | DOCUMENT ONLY |
| 27 | §42 — Verify evidence panel UI against 5-item checklist; Conflicts sub-panel | DOCUMENT ONLY now / FIX NOW after §37 |

### P3 — Documentation / traceability
*Improves clarity and judge-readability; doesn't block a working demo.*

| # | Item | Classification |
|---|---|---|
| 28 | §4 / §62 — Rewrite README/vision opening to lead with industrial framing | FIX NOW |
| 29 | §28 / §57 — Remap feature matrix to 5-tier vocabulary + expand to 26-row/6-column format | FIX NOW |
| 30 | §13 — Write model router's actual scoring/combination logic | FIX NOW |
| 31 | §34 — Add explicit 13-item coverage map to system architecture doc | DOCUMENT ONLY |
| 32 | §40 — Add Workflows/Reports nav routes (Assets already covered in P1) | FIX NOW |
| 33 | §49 — Add explicit Industrial Intelligence phase to build plan | FIX NOW |
| 34 | §51 — Add TEST-REVISION-001 for the already-complete §8 capability | FIX NOW |
| 35 | §53 — Add Claim/Revision/Verification/Reranking glossary terms | FIX NOW |
| 36 | §29 — Reconcile MVP scope additions (admin/observability/backup) against §29's 16-item list | DOCUMENT ONLY |
| 37 | §11 — Write verification pipeline skeleton (with TBD markers for contradiction/authority checks) | DOCUMENT ONLY |

### P4 — Future / non-essential
*Explicitly deferred, either by the master prompt's own text or by cost/benefit.*

| # | Item | Classification |
|---|---|---|
| 38 | §33 / §58 — 300-file template-to-canonical-reference restructuring | FUTURE (prototype the template now on 2-3 files, roll out later) |
| 39 | §27 — Renumber/relabel coding-agent and spreadsheet demos as a supporting-capabilities appendix | DOCUMENT ONLY, low urgency |
| 40 | §50 — Demo 3 (contradiction) and Demo 4 (asset trace) scripts | FUTURE, blocked on P1 |
| 41 | §56 — Full directory reorganization to the `00-overview/`...`12-sih/` scheme | FUTURE / not required — master prompt explicitly permits skipping this |
| 42 | §30 — Per-file MUST IMPLEMENT/STUB/OPTIONAL/FUTURE tagging across all ~300 feature files | FUTURE (group-level fix in P3 #29 covers the essential need) |
| 43 | §51 — TEST-CONTRADICTION-001 | FUTURE, blocked on §9 |

---

## Suggested execution order

Given the dependency chains uncovered above, the actual build order that minimizes rework is:
**P0 items 1–3 (assembly/writing, no dependencies) → §6 → §37 → §7, §9/§39, §38, §43, §10, §44(partial), §53(Asset), §5/§34 (all now unblocked) → remaining P2 items (independent of P1) → P3 → P4.**

This is different from strict P0→P1→P2→P3→P4 numeric order in one respect: several P2 items
have zero dependency on P1 and are cheap, so they can run in parallel with P1 rather than
strictly after it, if you have more than one work-thread available.
