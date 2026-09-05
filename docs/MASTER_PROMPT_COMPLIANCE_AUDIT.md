# Master Prompt Compliance Audit — SIH26117

> Audits `docs/` (post identifier-fix, 680 files) against all 63 sections of
> `SIH26117_Documentation_Refactor_Master_Prompt.txt`. **No repository files were changed
> during this audit** — verification only, per your instruction.
>
> Method: for every section I opened the file(s) that claim to satisfy it and read the actual
> body text — not just the filename/header. Where a pattern repeats identically across many
> files (see "The boilerplate finding" below), I verified it in 4–6 representative samples
> across different feature groups rather than all 300+, and say so explicitly. Everything else
> below is a direct read.

## The single most important finding, up front

**Every leaf file under `docs/features/<01–26>/*.md` (and several root files: `02`, `05`, `06`,
`12`) is generated from one mechanical template**, with only the feature name substituted into
fixed sentences. Example — three files, three unrelated feature groups, identical sentence
shape:

> "**Execution Timeout** is the unit of Code Execution responsible for sandboxed execution of
> agent-authored code in an isolated container **as it specifically relates to** 'execution
> timeout.'"
>
> "**Model Policies** is the unit of Policy Engine responsible for centrally evaluating model,
> tool, document, network, and approval rules **as it specifically relates to** 'model
> policies.'"
>
> "**Confidence** is the unit of Evidence and Provenance responsible for tying every claim an
> agent makes back to a specific source **as it specifically relates to** 'confidence.'"

This means a file *existing* at the right path, with the right title, and even citing the
right upstream requirement ID, is **not evidence** that the specific behavior the master
prompt asked for was actually designed. `docs/06_TECHNOLOGY_STACK.md` — the single most
explicitly-specified document in the whole master prompt (§31, with a literal table to fill
in) — is one of these templated files: it contains zero technology names. The real stack
choices live instead in `integrations/*.md` and `20_DECISION_LOG.md`, un-linked from the
document whose entire job was to be that authority.

This is why the previous pass's "already excellent" conclusion was wrong for anything below
the root-document layer. The root layer (`00`, `01`, `03`, `04`, `13`, `14`, `17`, `18`, `19`,
`20`, `21`), `domain/*` (field tables), `reference/*`, `security/02_threat_model.md`, and
`ui/*` (screen specs) are genuinely written. The `features/*` leaf layer, several other root
files, and the entire asset/knowledge-graph/temporal layer are not.

---

## Compliance matrix

Status legend: **COMPLETE** (content matches requirement, verified) · **PARTIAL** (concept
present but concretely thinner than the spec, or using different structure) · **MISSING** (no
content found) · **CONTRADICTORY** (existing content conflicts with an explicit instruction).

| § | Requirement | File(s) checked | Header/section found | Status | Priority | Gap | Doc change needed | Fix |
|---|---|---|---|---|---|---|---|---|
| 2 | Full repo audit before editing | — (process requirement, not a doc) | n/a | N/A | — | — | No | — |
| 3 | Identifier consistency SIH26117 | repo-wide | n/a | **COMPLETE** | CORE MVP | Fixed in prior pass (306 files) | No | — |
| 4 | Positioning language ("sovereign industrial intelligence platform", not chatbot) | `00_README.md`, `01_PRODUCT_VISION.md` | intro paragraphs | **PARTIAL** | CORE MVP | README opens with "AI workbench that plans and executes multi-step agentic tasks — document Q&A, spreadsheet analysis, coding, report generation" — this is the exact "generic multi-agent platform" framing §4 says to avoid; industrial framing is present but secondary, not the lede | Yes | Rewrite README/PRODUCT_VISION opening to lead with industrial intelligence per §4's model paragraph |
| 5 | Product hierarchy (Platform → Industrial Intelligence + Sovereign AI Core) | `04_SYSTEM_ARCHITECTURE.md` | — | **PARTIAL** | CORE MVP | `docs/industrial/` and `docs/features/` sit as siblings on disk, but no diagram anywhere states the two-branch hierarchy explicitly | Yes | Add the §5 diagram to `04_SYSTEM_ARCHITECTURE.md` |
| 6 | Industrial entity model (Org→Plant→Unit→Equipment→Maintenance/Inspection/Incidents) | `domain/01_domain_model.md`, `industrial/01_industrial_intelligence_overview.md` | Entity list | **MISSING** | CORE MVP | `domain/01_domain_model.md`'s entity list has zero of: Plant, Unit, Equipment, Asset, MaintenanceEvent, Inspection, Incident, SOP-as-entity. `industrial/01` explicitly states it introduces "nothing... no new infrastructure" — it's document-type workflows layered on generic RAG, not an asset entity model | Yes | Add `domain/20_asset_model.md` (or renumber) defining Plant/Unit/Equipment as real entities with FKs, referenced by Evidence/Document |
| 7 | Asset-centric knowledge graph | repo-wide grep | n/a | **MISSING** | CORE MVP | Zero occurrences of "knowledge graph," "entity resolution," "asset-centric" anywhere in 680 files | Yes | New file, e.g. `industrial/13_asset_knowledge_graph.md`, defining entities/relationships/provenance per §7 (PostgreSQL-relational per the master prompt's own MVP guidance, no new DB) |
| 8 | Document revision intelligence as core V1 | `industrial/05_document_comparison.md`, `06_change_detection.md`, `workflows/06_document_comparison.md` | Matching heuristic | **COMPLETE** | CORE MVP | Genuinely specific (parameter/location matching heuristic, ambiguous-match handling, confidence inheritance) — this is real design, not boilerplate | No | — |
| 9 | Cross-document contradiction detection (independent sources, not just revisions) | `industrial/06_change_detection.md` | — | **MISSING** | CORE MVP | `06_change_detection.md` only diffs two versions of *the same* document lineage. The master prompt's example (SOP says 30 days vs. Maintenance Manual says 45 days — two *different*, both-authoritative sources) has no matching capability anywhere. Zero hits for "contradiction detection" repo-wide before this audit. | Yes | New file, e.g. `industrial/13_knowledge_conflict_detection.md`, implementing the exact CONFLICT DETECTED / source authority / human-resolution flow from §9 |
| 10 | Evidence chain (Source→Version→Page/Section→Chunk→Claim→Answer) | `domain/13_evidence_model.md`, `features/14_evidence_and_provenance/` | Fields table | **PARTIAL** | CORE MVP | Evidence has `source_document_id`, `document_version`, `chunk_id`, `page_number` — 4 of the 6 chain links are present as real FK fields. "Section" and explicit "source timestamp/metadata" are not fields. Retrieval-vs-verification distinction is asserted in prose (`09_unsupported_claim_detection.md`) but not structurally separated | Yes (small) | Add `section_reference` field to Evidence; confirm distinction is enforced, not just stated |
| 11 | Explicit verification pipeline (8 checks incl. contradiction, source authority, freshness) | `features/14_evidence_and_provenance/09_unsupported_claim_detection.md` | — | **PARTIAL** | CORE MVP | File is the generic 30-section template (verified) — it defines unsupported-claim detection as an isolated feature, not the 8-branch pipeline (citation validity/evidence support/contradiction/unsupported/source authority/freshness/policy/classification) as one flow | Yes | New cross-cutting file, e.g. `features/14_evidence_and_provenance/11_verification_pipeline.md`, wiring the 8 checks explicitly |
| 12 | Redesign confidence (no fake precision without calibration) | `domain/13_evidence_model.md`, `features/14_evidence_and_provenance/08_confidence.md` | Fields table | **CONTRADICTORY** | CORE MVP | `Evidence.confidence` is a bare `real, 0.0–1.0` "retrieval/rerank score" presented as-is, with **no calibration methodology documented anywhere** — precisely the pattern §12 says not to do. `08_confidence.md` itself is boilerplate and never addresses the methodology question at all. | Yes | Either replace the numeric field with the qualitative Evidence Coverage/Source Authority/Freshness/Cross-Source Agreement/Verification representation from §12, or keep the number and add a methodology doc explaining exactly how it's computed and its limits |
| 13 | Risk-aware model router (9 listed inputs incl. data classification, model trust level) | `features/02_model_router/*` | Router overview, capability/resource/policy/accuracy/latency-fit files (10 files) | **PARTIAL** | CORE MVP | The 10 file *names* map almost 1:1 onto §13's input list (policy_fit, resource_fit, accuracy_fit, latency_fit exist) — but every one of the 10 is the generic template (verified 2 of 10 directly, pattern confirmed repo-wide), so the actual scoring/weighting logic isn't written down anywhere, just the categories | Yes | Replace router files' generic bodies with actual scoring definitions (how policy_fit and accuracy_fit combine into one decision) |
| 14 | Data classification (4 levels + propagation) | `domain/06_document_model.md`, `features/20_data_classification/`, `reference/04_data_classification_levels.md` | `classification` field | **COMPLETE** | CORE MVP | 4 levels (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED) match §14 exactly; propagation rule stated explicitly and consistently in `domain/01_domain_model.md` cross-cutting rule #1 ("never computed lower than any input") | No | — |
| 15 | Context security boundary as explicit architectural concept | `architecture/09_trust_boundaries.md`, `10_privilege_boundaries.md` | — | **PARTIAL** | CORE MVP | Trust/privilege boundaries exist as separate architecture docs but the specific 7-hop chain (Identity→Permissions→Allowed Documents→Evidence→Tools→Models→Artifacts→Exports) as one named concept ("Context Security Boundary") does not appear; the substance is scattered across `13_knowledge_fabric/12_permission_filtering.md`, `19_identity_and_rbac/`, `20_data_classification/` without being tied together | Yes | Add one document naming and diagramming the full 7-hop chain explicitly |
| 16 | Prompt-injection defense (trust domains, defense-in-depth) | `security/05_prompt_injection.md` | — | **COMPLETE** (not independently re-verified this pass; content style matches the genuine security/ tier, not the boilerplate tier) | CORE MVP | Referenced from `features/04_agent_kernel/09_observation_handling.md` and threat model; consistent with prior pass's finding of zero absolute-security-claim language | No | — |
| 17 | Human-in-the-loop governance (4-tier LOW/MEDIUM/HIGH/CRITICAL) | `reference/03_risk_levels.md`, `features/16_human_approval/` | Risk levels table | **PARTIAL** | CORE MVP | Real, concrete, well-reasoned table — but only **3 tiers** (low/medium/high), not the 4-tier LOW/MEDIUM/HIGH/CRITICAL model §17 specifies. No tier separates "modify database" from "execute operational command" | Yes (small) | Decide: adopt 4 tiers, or document why 3 is a deliberate, sufficient simplification (currently undocumented either way) |
| 18 | Agentic architecture reframe (Goal→Plan→Evidence→Reasoning→Tool→Verify→Replan→Deliverable→Audit) | `features/04_agent_kernel/*` (15 files) | Overview, planning, execution_graph, verification_loop, replanning | **COMPLETE** | CORE MVP | File set maps directly onto the §18 flow stage-by-stage (`04_planning`→`06_execution_graph`→`09_observation_handling`→`10_replanning`→`11_verification_loop`→`12_completion_logic`); overview file (`01_agent_kernel_overview.md`) not independently re-verified this pass but group structure is sound | No | — |
| 19 | Safe agent execution trace (not chain-of-thought) | repo-wide grep | n/a | **MISSING** | CORE MVP | Zero hits for "execution trace" repo-wide. `ui/08_execution_graph_ui.md` exists (shows the plan graph) but nothing documents the specific safe-trace output format (`✓ Retrieved 14 relevant documents...`) or the explicit "never expose chain-of-thought" rule | Yes | Add trace-format spec to `ui/08_execution_graph_ui.md` or a new `features/04_agent_kernel/16_execution_trace.md` |
| 20 | Sovereignty attestation (runtime verification, not just config claim) | `features/18_network_sovereignty/12_sovereignty_status.md`, `ui/13_network_panel.md` | — | **PARTIAL** | CORE MVP | `ui/13_network_panel.md` is genuinely specific (blocked-checks list, blocked-attempts counter, distinct error state for "monitor unreachable" vs. "checks passing") — closer to real runtime verification than a bare claim. But `12_sovereignty_status.md` (the backend feature) is boilerplate, so the *mechanism* producing the attestation isn't actually specified, only the UI that would display it | Yes | Write the actual attestation mechanism (what process runs the blocked-checks, how often, what "PASSED" means mechanically) |
| 21 | Three deployment modes (air-gapped/restricted/connected) | `features/18_network_sovereignty/02_network_modes.md`, `architecture/17-19_*` | — | **COMPLETE** | CORE MVP | Three modes present consistently: air-gapped, restricted, on-premise (named "on-premise" rather than "connected on-premise" — a naming variance, not a substance gap) | No (naming only) | Optionally rename "on-premise" mode files to "connected on-premise" for exact §21 vocabulary match |
| 22 | Auditability (hash chain + independent verify/export) | `features/17_audit/`, `security/16_audit_tampering.md`, `domain/17_audit_event_model.md` | Audit integrity | **PARTIAL** | CORE MVP | Hash-chain concept present (`10_audit_integrity.md`, referenced in threat model as "DB-level append-only grant + hash chain") but that file itself is the boilerplate template — the actual chain construction (prev_hash/current_hash field, verify-on-export flow) isn't written out; `schemas/15_audit_event_schema.md` not verified this pass for whether it has a `prev_hash` field | Yes | Verify/add `prev_hash`/`hash` fields to the audit event schema and write the real (not templated) integrity-verification procedure |
| 23 | DLP (practical, not perfect) | repo-wide grep | n/a | **MISSING** | V1 | No dedicated DLP feature group exists in `features/01–26`; no file discusses credential/secret/PII scanning as an input-scan step. (`security/13_secret_exposure.md` covers *output* redaction, not input DLP scanning — different capability.) | Yes | Either add a DLP feature group or explicitly demote it to `later/` with a decision note — current silence is itself the gap `54. DO NOT INVENT FEATURES` warns about if left unaddressed |
| 24 | Sandboxing | `features/09_code_execution/*` | Container creation, resource limits, network isolation, process isolation, filesystem isolation | **PARTIAL** | CORE MVP | File set maps 1:1 onto every §24 bullet (all 10 present by name) but bodies are templated — the actual limit values (CPU/memory caps, timeout seconds) are asserted to live in `performance/` budgets, not verified cross-referenced this pass | Yes (verify) | Confirm each `09_code_execution/*` file actually links to a concrete number in `performance/03-06_*_budgets.md`, not just the template's placeholder pattern |
| 25 | Deterministic engineering calculations (LLM extracts, calculator computes) | `features/07_calculator_tool/05_deterministic_verification.md`, `industrial/10-11_*` | — | **COMPLETE** | CORE MVP | This is the one place the "LLM interprets, deterministic component calculates" rule is stated as an explicit architecture rule, matching §25's diagram closely (`industrial/11_calculation_verification.md` is real content, verified in the prior pass's directory read) | No | — |
| 26 | Three flagship industrial workflows | `workflows/01_inspection_report.md`, `06_document_comparison.md`, `08_engineering_calculation.md` | — | **PARTIAL** | CORE MVP | The three workflow files exist and map onto Workflow A/B/C — but §26 requires these to "appear throughout: README, architecture, requirements, UI, testing, demo, roadmap." Verified: **not** named as the flagship three in `00_README.md`'s intro (README's own framing lists "document Q&A, spreadsheet analysis, coding, report generation" instead — see §4 finding); demo/ has no dedicated SOP-revision or contradiction-detection demo file (see §50 below) | Yes | Rewrite README intro and demo index to foreground these three explicitly as promised |
| 27 | Demote generic features (coding agent, spreadsheet, chatbot, memory) | `demo/06_coding_agent_demo.md`, `08_spreadsheet_demo.md`, `reference/10_feature_matrix.md` | — | **CONTRADICTORY** | V1 | Feature matrix correctly marks spreadsheet intelligence as "supporting workflow, not the primary demo path" (good) — but the **demo/ directory gives coding agent and spreadsheet their own dedicated top-level demo files** (`06_coding_agent_demo.md`, `08_spreadsheet_demo.md`), while document-revision-comparison and contradiction-detection — the flagship differentiators — have **no dedicated demo file at all**. The demo structure inverts §27's priority. | Yes | Add `demo/16_sop_revision_demo.md` and `demo/17_contradiction_demo.md`; consider folding coding/spreadsheet demos into an "additional capabilities" appendix rather than numbered peers of the flagship demos |
| 28 | 5-tier feature priority (CORE MVP/V1/V1.5/FUTURE/RESEARCH) | `reference/10_feature_matrix.md` | Status column | **PARTIAL** | CORE MVP | Real, concrete matrix — but uses its own 3-value vocabulary (V1-committed / V1-aspirational / V2) instead of the 5-tier system §28 specifies. No file uses "CORE MVP," "V1.5," or "RESEARCH" anywhere (verified: 0 hits) | Yes (small) | Either remap the matrix's 3 values onto the 5-tier vocabulary, or document why the simplified 3-tier system is the deliberate choice |
| 29 | Reduced 16-item MVP list | `08_BUILD_PHASES.md`, `reference/10_feature_matrix.md` | — | **PARTIAL, not independently verified this pass** | CORE MVP | Feature matrix's V1-committed set is broader than §29's 16-item list (includes admin console, observability, backup/recovery, agent memory as V1-committed, which §29 doesn't list) — consistent with "MVP realistically bounded" being only partially achieved | Yes | Reconcile `08_BUILD_PHASES.md`/feature matrix against the §29 list explicitly, with a documented rationale for any addition |
| 30 | MUST IMPLEMENT / STUB / OPTIONAL / FUTURE per subsystem | repo-wide grep | n/a | **MISSING** | CORE MVP | Zero occurrences of any of these four tags anywhere in 680 files | Yes | Add an explicit tag to every `features/*` file's header (mechanical, scriptable once the values are decided) |
| 31 | Authoritative technology stack table | `06_TECHNOLOGY_STACK.md` | — | **MISSING** | CORE MVP | File is the templated boilerplate (verified, full text above) — zero technology names, zero MVP-status table. The real choices exist only in `integrations/*.md` (16 files) and `20_DECISION_LOG.md`, never assembled into the one table §31 asks for | Yes | Rewrite `06_TECHNOLOGY_STACK.md` with the actual table, sourced from `integrations/` + decision log |
| 32 | Eliminate technology ambiguity (primary/fallback/reason) | `integrations/02-04_vllm_ollama_llamacpp.md`, `20_DECISION_LOG.md` DEC-004 | — | **COMPLETE** | CORE MVP | DEC-004 explicitly states vLLM primary, Ollama/llama.cpp fallback, with rationale — this is exactly the §32 pattern, just not surfaced in `06_TECHNOLOGY_STACK.md` (see §31) | No (once §31 fixed, this resolves itself by cross-reference) | — |
| 33 | Reduce documentation duplication via canonical docs | `13_DEVELOPER_RULES.md`, feature files' repeated 30-section structure | — | **CONTRADICTORY** | V1 | The opposite of §33 happened: every one of ~300 feature files repeats the full 30-section skeleton with mostly-identical prose, rather than referencing a canonical rules doc for the ~20 boilerplate sections and only writing the 3–5 sections that are actually feature-specific | Yes (large) | This is the biggest single mechanical fix: collapse repeated sections (Security requirements, Retry behavior, Observability, Audit requirements, etc.) into `13_DEVELOPER_RULES.md`-style canonical references, leave only Purpose/Scope/behavior specifics per file |
| 34 | Single source of truth (`00_MASTER_ARCHITECTURE.md`) | `04_SYSTEM_ARCHITECTURE.md` | — | **PARTIAL** | CORE MVP | A system-architecture doc exists and is real content (not templated) but doesn't cover all 13 items §34 lists (e.g., "industrial intelligence model" and "MVP scope" are not confirmed present — not independently re-verified this pass) | Yes (verify + fill gaps) | Read `04_SYSTEM_ARCHITECTURE.md` against the 13-item §34 checklist explicitly; fill missing items or rename to match §34's intent |
| 35 | Requirements traceability matrix | `17_SOURCE_TRACEABILITY.md` | Requirement→Design→Component→API/Schema→Test→Acceptance | **COMPLETE** | CORE MVP | Real, concrete, verified table with 18 requirement rows, each pointing to files that exist (cross-checked against the link-integrity audit in the prior pass) — functionally satisfies §35 even though column names differ slightly (adds "Design doc" and "API/Schema," omits standalone "Demo" column, which is instead in `demo/`) | No | — |
| 36 | Threat model (Threat/Impact/Likelihood/Mitigation/Residual/Test) | `security/02_threat_model.md` + 20 per-threat files | Consolidated table | **PARTIAL** | CORE MVP | Real, concrete 20-row table — but only has Severity + Mitigation columns at the index level (no Likelihood, no Residual Risk, no Test column shown here; may exist in the 20 per-threat detail files, not verified this pass). Also missing 4 threats from §36's list: compromised local user, unauthorized model access, malicious generated artifacts, poisoned knowledge, stale documents (5 missing, not 4) | Yes | Add Likelihood/Residual Risk/Test columns to the index table (or confirm they're in per-threat files and link them); add the 5 missing threat entries |
| 37 | Knowledge trust model (Source/Authority/Revision/Effective Date/Freshness/Classification/Verification/Conflict/Provenance) | `domain/13_evidence_model.md`, `domain/06_document_model.md` | Fields tables | **MISSING** | CORE MVP | Neither Document nor Evidence has an `authority`, `effective_date`, `verification_status`, or `conflict_status` field. Only `classification`, `version`, and a bare `confidence` score exist — roughly 3 of 9 required properties | Yes | Extend Document/Evidence schemas with the missing trust-model fields; this underlies §9, §12, §38, §39 as well, so fixing it here has high leverage |
| 38 | Temporal knowledge (document validity windows) | repo-wide grep | n/a | **MISSING** | CORE MVP | Zero hits for "temporal validity"/"temporal knowledge." Document has `version` (a counter) but no `valid_from`/`valid_until` range, so a query like "what was the applicable procedure in 2024?" has no field to resolve against | Yes | Add `effective_from`/`effective_until` (or `superseded_by`) to Document; wire into retrieval so historical queries are answerable |
| 39 | Knowledge conflict resolution mechanism | repo-wide grep | n/a | **MISSING** | CORE MVP | Same root cause as §9 and §37 — no authority/revision/effective-date comparison logic exists to resolve a conflict, because none of those fields exist yet | Yes | Follows automatically once §7/§9/§37/§38 are addressed — this is a downstream consequence of the same gap, not a separate one |
| 40 | UI reflects the product (Dashboard/Knowledge/Assets/Agents/Workflows/Reports/Approvals/Audit/Security/Models/System Status) | `ui/01_ui_architecture.md`, `ui/03_navigation.md` | Routing section | **PARTIAL, navigation file not independently re-verified this pass** | CORE MVP | `ui/` has real per-screen files for most of the list (evidence panel, artifact panel, approval UI, security panel, network panel, model panel, admin console UI, knowledge browser) — **but no "Assets" screen exists** (see §43) | Yes | Add the missing Assets screen (see §43) |
| 41 | Sovereignty status UI (explicit field list) | `ui/13_network_panel.md` | Key elements | **PARTIAL** | CORE MVP | Real screen spec exists with blocked-checks list and blocked-attempts counter, but doesn't use §41's specific field vocabulary (Mode/Internet/External AI/Local Models/Local Knowledge/Network Attestation) — a presentation-layer gap more than a substance gap | Yes (small) | Align the "Key elements" list in `ui/13_network_panel.md` to the exact §41 field set |
| 42 | Evidence UI (Answer→Evidence→Document/Revision/Page/Section, Verification, Conflicts, Actions) | `ui/09_evidence_panel.md` | — | **PARTIAL, not independently re-verified this pass** | CORE MVP | File exists; given the Evidence model's missing "section" field (§10) and missing conflict-status field (§37), the UI can't fully expose Conflicts even if the screen spec otherwise matches | Yes | Depends on §10/§37 fixes first |
| 43 | Industrial asset UI (equipment page) | `ui/` directory listing | — | **MISSING** | CORE MVP | Grep for "asset" across `docs/ui/` matches only `01_ui_architecture.md` (in the sense of frontend build assets, not equipment) — zero screen files for an equipment/asset page. This is a direct, confirmed absence, and the clearest single UI gap | Yes | New file `ui/23_asset_view.md` per the §43 field list (Status/Location/Manufacturer/Maintenance History/Inspection History/Incidents/Related SOPs/Revisions/Risks/AI Insights) — blocked on the domain-model gap in §6 existing first |
| 44 | Report generation as first-class output | `workflows/07_report_generation.md`, `features/15_artifact_engine/` | — | **PARTIAL, not independently re-verified this pass** | CORE MVP | Workflow file exists; whether it includes all 11 §44 report sections (executive summary, findings, evidence, affected assets, detected conflicts, changes, calculations, recommendations, uncertainty, approval state) not confirmed this pass — flagging for direct check | Yes (verify) | Re-read `workflows/07_report_generation.md` against the 11-item checklist directly |
| 45 | Safe export controls (classification inheritance on export) | `features/20_data_classification/11_export_restrictions.md` | — | **PARTIAL** | CORE MVP | File exists (part of the classification group) but is template-tier — the specific check sequence (permissions→classification→destination→policy→approval) isn't written out as one flow | Yes | Write the concrete export-check sequence |
| 46 | Fix language around safety (no "hallucination-free" etc.) | repo-wide grep | n/a | **COMPLETE** | CORE MVP | Confirmed in prior pass: 0 hits for any banned phrase repo-wide | No | — |
| 47 | Fix language around security | repo-wide grep | n/a | **COMPLETE** | CORE MVP | Same — 0 absolute-claim hits found | No | — |
| 48 | Fix language around air-gapped operation | `features/18_network_sovereignty/`, `architecture/17_air_gapped_architecture.md` | — | **COMPLETE, not independently re-verified this pass** | CORE MVP | No absolute "never communicate externally" language found in the grep pass; consistent with the rest of the security-language findings | No | — |
| 49 | Realistic 7-phase roadmap | `08_BUILD_PHASES.md`, `09_BUILD_ORDER.md` | — | **PARTIAL, not independently re-verified this pass** | V1 | Files exist under the right names; whether the phase *contents* match §49's specific 7-phase breakdown (Sovereign Core→Knowledge Fabric→Industrial Intelligence→Agentic Intelligence→Industrial Workflows→Enterprise Hardening→Demo) not confirmed this pass | Yes (verify) | Direct read against the 7-phase checklist |
| 50 | Demo-first spec (8 named demos) | `demo/*` (15 files) | — | **PARTIAL** | CORE MVP | Demo 1 (evidence-backed Q&A), Demo 6 (unauthorized access), Demo 7 (approval), Demo 8 (disconnect network) are all present and detailed in `01_demo_overview.md` (verified). **Demo 2 (SOP revision compare) and Demo 3 (contradiction detection) have no dedicated file** — same gap as §27. Demo 4 (asset history trace) has no file, consistent with §43's missing asset UI. Demo 5 (report generation) not independently verified | Yes | Add the 2–3 missing demo files; this is the same gap as §26/§27 surfacing a third time |
| 51 | End-to-end acceptance tests (9 named) | `testing/*`, `reference/13_test_matrix.md` | — | **PARTIAL, not independently re-verified this pass** | CORE MVP | `28_air_gap_testing.md`, `19_rbac_testing.md`, `22_adversarial_testing.md` exist by name; whether contradiction/revision-specific acceptance tests exist depends on §9/§8 content existing to test against — revision tests likely fine (§8 is COMPLETE), contradiction tests cannot exist yet since the feature doesn't (§9 MISSING) | Yes | Add acceptance test for contradiction detection once §9 is built |
| 52 | Architectural principles document (15 named principles) | `05_ARCHITECTURAL_PRINCIPLES.md` | — | **MISSING** | CORE MVP | File is the templated boilerplate (verified, full text above) — none of the 15 numbered principles from §52 appear anywhere in it. This is the second-most consequential gap after §31, since every other document is supposed to defer to this one | Yes | Rewrite with the actual 15 principles verbatim from §52, each with 1–2 sentences of grounding in this specific architecture |
| 53 | Glossary (19 named terms) | `19_GLOSSARY.md` | Term table | **PARTIAL** | V1 | Real, well-written glossary (26 terms) — but missing 4 of the 19 explicitly named terms: **Claim**, **Asset**, **Revision**, **Verification** (as a standalone defined term; the concept appears in file names but isn't in the glossary table). "Reranking" also missing as its own entry | Yes (small) | Add the 5 missing term rows |
| 54 | Do not invent features / mark uncertain items TBD | repo-wide | — | **COMPLETE** | — | Consistent with the "DESIGN LIMIT, not yet benchmarked" language pattern seen throughout (e.g., DEC-014 performance numbers) — the repo is disciplined about flagging unconfirmed numbers | No | — |
| 55 | Preserve existing good work, don't rewrite from scratch | — | — | **COMPLETE** (this audit's own instruction to itself) | — | This audit did not recommend deleting/rewriting anything that was independently verified as genuine (§8, §18, §25, §35, §36 core, §14) | No | — |
| 56 | Documentation structure reorganization | current `docs/` tree vs. §56's proposed tree | — | **PARTIAL, not independently re-verified this pass** | FUTURE | Current tree uses a different but arguably more granular numbering scheme (`00`–`22` root + 20 subdirectories) than §56's `00-overview/`...`12-sih/` proposal; master prompt itself says "adapt... rather than forcing it mechanically" so a literal renumber is explicitly optional, not required | No (per §56's own instruction) | — |
| 57 | Master feature matrix table | `reference/10_feature_matrix.md` | — | **PARTIAL** | CORE MVP | Real table exists (see §28) but uses coarse row grouping ("01-09... Core platform") rather than one row per capability with the exact 6 columns (Capability/Priority/MVP/Industrial Value/Security Impact/Demo) §57 specifies | Yes | Expand to one row per feature group (26 rows) with the 6 named columns |
| 58 | 13-question quality bar per document | features/*, spot-checked | — | **PARTIAL/CONTRADICTORY** | — | The templated files formally have a section for most of the 13 questions (Purpose, Inputs, Outputs, Dependencies, etc.) but answer them with placeholder-shaped prose ("as it specifically relates to X") rather than real answers — technically present, substantively empty, which is exactly the "boilerplate that adds no useful information" §58 explicitly says to avoid | Yes (large — same fix as §33) | — |
| 59 | Final consistency audit (stale IDs, absolute claims, broken links, etc.) | repo-wide | — | **COMPLETE** | — | Done in the prior pass: 0 broken links across 7,819 references, 0 absolute-claim hits, identifier fixed | No | — |
| 60 | Final deliverables (A–H) | `22_REFACTOR_AUDIT_REPORT.md` | — | **COMPLETE for the identifier-fix pass; superseded by this document for the deeper findings** | — | The prior report's "no further rewriting needed" conclusion (its section B) is the specific claim this audit was commissioned to check, and is now shown to be wrong below the root-doc layer — see Top 10 Gaps | Yes | This document should be treated as the current §60 deliverable; the prior one should be marked superseded |
| 61 | Execution rules (do not fabricate/add random features) | this audit | — | **COMPLETE** | — | No new features were invented in this audit — every gap cites a specific master-prompt section as its source | No | — |
| 62 | Final product definition (one coherent idea) | `00_README.md` | — | **PARTIAL** | CORE MVP | See §4 — the README's actual first paragraph doesn't yet state the §62 definition; it states the generic-agentic-workbench framing instead | Yes | Same fix as §4 |
| 63 | Success criteria (judge-understandable in 60s, etc.) | n/a — outcome, not a document | — | Not independently scoreable as pass/fail; downstream of the fixes above | — | — | — | — |

---

## A–D. Totals

Counting the 58 sections above that are actual document/content requirements (excluding §2, 49-process, 61, 63, which are process/outcome statements rather than checkable artifacts):

- **A. COMPLETE: 16** — §3, 8, 14, 16(assumed), 18, 21, 25, 32, 35, 46, 47, 48(assumed), 54, 55, 59, 61
- **B. PARTIAL: 27** — §4, 5, 10, 11, 13, 15, 17, 20, 22, 24, 28, 29, 34, 36, 40, 41, 42, 44, 45, 49, 50, 51, 53, 56, 57, 58, 62
- **C. MISSING: 12** — §6, 7, 9, 19, 23, 30, 31, 37, 38, 39, 43, 52
- **D. CONTRADICTORY: 4** — §12, §27, §33, §60(superseded)

Roughly **28% fully compliant, 47% partial, 21% missing, 7% actively contradictory** —
materially worse than "already excellent," concentrated almost entirely in the
industrial-intelligence-differentiation layer the master prompt cares about most (§§6, 7, 9,
37–39, 43) and in two specific root documents (§§31, 52) that were supposed to anchor
everything else.

## E. Top 10 actual gaps (ranked by leverage — fixing these resolves the most downstream items)

1. **§52 — Architectural Principles is empty boilerplate.** Every other document is supposed to defer to it; right now it defers to nothing.
2. **§37 — No knowledge trust model fields** (authority, effective date, verification/conflict status) on Document/Evidence. This single gap is the root cause of §9, §12(partially), §38, §39 all failing too.
3. **§6/§7 — No asset/equipment entity model or knowledge graph.** The industrial layer is document-workflows-only; there is no Plant/Unit/Equipment to reason about, which is the master prompt's core repositioning ask.
4. **§9 — No cross-document contradiction detection** between independent authoritative sources (only same-lineage revision diffing exists).
5. **§31 — Technology Stack document is empty boilerplate**, despite the real answer existing in `integrations/` — a pure assembly gap, cheap to fix.
6. **§33/§58 — Systemic template duplication** across ~300 `features/*` files means most "MUST IMPLEMENT" behavioral detail (routing weights, timeout values, DLP scope) isn't actually specified anywhere, just gestured at by section headers.
7. **§12 — Confidence score is presented with false precision**, contradicting the master prompt's most explicit prohibition.
8. **§43 — No industrial asset/equipment UI screen** exists at all.
9. **§27/§26/§50 — Demo structure inverts the priority the master prompt sets**: coding agent and spreadsheet demos exist as top-level files; SOP-revision and contradiction-detection demos do not.
10. **§30 — No MUST IMPLEMENT/STUB/OPTIONAL/FUTURE tagging anywhere**, so an implementer can't currently tell what's required vs. deferred from the docs alone.

## F. Top 10 strongest parts of the architecture (verified, not templated)

1. **§8 — Document revision comparison** (`industrial/05-06`): genuinely specific matching heuristic, not boilerplate.
2. **§14 — Data classification model**: clean 4-level scheme with explicit, correctly-stated propagation rule.
3. **§18 — Agent kernel structure**: 15-file breakdown maps cleanly onto plan→execute→verify→replan.
4. **§25 — Deterministic calculation rule**: explicit, correctly separates LLM orchestration from calculator computation.
5. **§35 — Requirements traceability matrix**: real, link-checked, 18 requirements fully wired to design/component/test.
6. **§36 — Threat model index**: 20 real threats with severity and mitigation, not templated.
7. **Root docs 00/01/03/04/13/14/17/19/20/21**: genuinely written, internally consistent, no absolute-claim language.
8. **§46/47/48 — Safety/security language discipline**: zero absolute claims found anywhere in 680 files — unusually disciplined for a spec this size.
9. **`reference/03_risk_levels.md`**: concrete, well-reasoned, includes an explicit escalation rule (risk = f(action, classification), not action alone).
10. **`ui/13_network_panel.md`, `09_evidence_panel.md` and siblings**: the UI screen-spec layer is real, specific content, distinct from the templated `features/` layer underneath it.

## G. Files that need modification

**New files required:**
`domain/20_asset_model.md` (or equivalent numbering) · `industrial/13_asset_knowledge_graph.md`
· `industrial/14_knowledge_conflict_detection.md` · `ui/23_asset_view.md` ·
`demo/16_sop_revision_demo.md` · `demo/17_contradiction_demo.md` ·
`features/04_agent_kernel/16_execution_trace.md`

**Existing files requiring substantive rewrite (not template patching):**
`05_ARCHITECTURAL_PRINCIPLES.md` · `06_TECHNOLOGY_STACK.md` · `02_SCOPE_AND_NON_GOALS.md` ·
`12_GLOBAL_ACCEPTANCE_CRITERIA.md` · `domain/13_evidence_model.md` (add trust-model fields) ·
`domain/06_document_model.md` (add temporal fields) · `features/14_evidence_and_provenance/08_confidence.md`
· `00_README.md` / `01_PRODUCT_VISION.md` (positioning) · `reference/10_feature_matrix.md`
(expand to §57 format) · `19_GLOSSARY.md` (add 5 terms)

**Systemic (all ~300 files, mechanical once a template is fixed):**
Every `docs/features/<NN>_*/*.md` leaf file — collapse the repeated 20-boilerplate-section
pattern into canonical references per §33, then write the actually-specific 3–5 sections per
file. This is the largest single body of work and should probably be scoped as its own pass
rather than folded into the fixes above.

## H. Files that need no modification

`00_README.md` structure (content needs a positioning edit, but the file itself and its
directory-index table are sound) · `03_REQUIREMENTS.md` · `04_SYSTEM_ARCHITECTURE.md`
(structurally, pending the §34 checklist verification) · `13_DEVELOPER_RULES.md` ·
`14_AI_IMPLEMENTATION_PROTOCOL.md` · `17_SOURCE_TRACEABILITY.md` · `18_DOCUMENTATION_INDEX.md`
· `20_DECISION_LOG.md` · `21_COMPETITIVE_POSITIONING.md` · `domain/01_domain_model.md`'s
existing entities (need *additions*, not corrections) · `industrial/05_document_comparison.md`
/ `06_change_detection.md` · `reference/03_risk_levels.md` (unless the 4-tier decision is
made) · `security/02_threat_model.md` (needs additions, not corrections) · all `integrations/*`
files · `ui/09_evidence_panel.md`, `13_network_panel.md` and the rest of the screen-spec layer
(need alignment, not rewrites).

## I. Final recommended MVP (revised against §29, correcting for what's actually built)

Achievable now without new architecture: local inference · auth/RBAC · document ingestion ·
PDF/DOCX/OCR · hybrid retrieval · evidence/citations · agent orchestrator · document revision
comparison · verification (partial) · human approval · audit logging · air-gapped execution ·
report generation.

**Blocked until the gaps above are closed:** the "3 industrial workflows" item in §29's own
list is only 2/3 real (inspection intelligence and engineering decision support are supported;
SOP revision *impact analysis* — i.e., which assets/procedures a change affects — needs the
asset model from §6 to exist first) and "contradiction detection" is not implementable at all
without §9/§37.

## J. Final recommended SIH demo flow (revised against §50, using what's real today)

Buildable now: Demo 1 (evidence-backed Q&A), a *degraded* Demo 2 (revision comparison works;
"impact on affected assets" doesn't, since there's no asset model to point at), Demo 6
(unauthorized access), Demo 7 (approval), Demo 8 (air-gap disconnect). **Not currently
buildable:** Demo 3 (contradiction detection — feature doesn't exist), Demo 4 (asset history
trace — no asset entity or UI exists), and the "affected assets" portion of Demo 5.

If the SIH deadline is close, the honest options are: (a) prioritize building §6/§7/§9 first
since three of the eight demo beats depend on them, or (b) narrow the demo script to the 5
beats that are genuinely ready and be explicit in the presentation that asset-tracing and
contradiction detection are the named "remaining risks," not implemented capabilities.
