# Demo Overview (Canonical Runbook)

> **Canonical owner** of the exact, reproducible demo procedure. `docs/demo/05_..14_*.md`
> files hold sub-scenario detail; this file is the master sequence and the shared setup.

## Hardware / software for the demo

- Hardware: **PROFILE-B** (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`).
- Network mode: **`air_gapped`** (REQ-NET-002) — Wi-Fi/Ethernet physically disconnected or
  firewalled at the router level before the demo starts, so the sovereignty claim is provable
  independent of the application layer.
- Models: whichever checkpoints are pinned per `20_DECISION_LOG.md` DEC-013, already loaded
  and warmed (first-token latency excluded from the timed portion of the demo).
- User/role: demo runs as `Administrator` for the approval step, and separately as
  `Restricted User` for the RBAC-denial beat (DEC-006 — the two V1-rehearsed roles).

## Demo data

Defined in full in `demo/03_demo_data.md`; summary:
- One synthetic scanned "Industrial Inspection Report" PDF (10 pages, includes at least one
  page requiring OCR and one native-text page), containing a small number of clearly
  identifiable, deterministic "findings" (e.g. "Bolt torque on Flange B is 15% below spec on
  page 4") so the expected agent answer is known in advance.
- One synthetic equipment photograph for the multimodal beat.
- One small CSV/XLSX for the spreadsheet-adjacent beat (if included in the walkthrough).

No proprietary or real customer documents are used, per Upgrade Prompt §42.

## Primary scenario — Inspection Report Q&A with Evidence and Approval

1. **Import.** Administrator uploads the synthetic inspection report PDF via the workbench.
   Document enters `UPLOADED` (see `runtime/` state machines).
2. **Classify.** User tags the document `INTERNAL` classification.
3. **Extract/OCR.** System transitions `VALIDATING` → `EXTRACTING` → `OCR` (for scanned pages)
   → `INDEXING` → `READY`. Sovereignty panel remains green throughout.
4. **Ask.** User asks: *"What findings in this report indicate equipment below
   specification, and on what page?"*
5. **Retrieve + Evidence.** Agent kernel retrieves relevant chunks (`features/13_knowledge_fabric/`),
   generates an answer, and attaches `Evidence` records per REQ-FUNC-005.
6. **Display citations.** UI evidence panel shows each claim with its page reference; clicking
   a citation highlights the source passage.
7. **Generate approval note.** Agent proposes generating a DOCX "Findings Summary" artifact —
   classified `risk=medium` (artifact generation from INTERNAL data) per
   `reference/03_risk_levels.md`, so it proceeds without approval; if the demo instead uses a
   CONFIDENTIAL-tagged document, this step becomes `risk=high` and triggers step 8's gate.
8. **Human approval (if triggered).** If any step is `risk=high` (e.g. an export action), task
   enters `WAITING_APPROVAL`; Administrator approves via the Approval panel.
9. **Produce artifact.** Artifact Engine generates a real, valid `.docx` file
   (`features/15_artifact_engine/03_docx_generation.md`) containing the findings and citations.
10. **Show audit trail.** Audit viewer displays the complete event chain for this task:
    `document.uploaded` → ... → `document.indexed` → `task.created` → ... →
    `artifact.created` → `artifact.ready` → (`artifact.approved` if applicable).
11. **Show network monitor.** Sovereignty panel (`ui/13_network_panel.md`) has shown zero
    external connections for the full duration; operator may additionally show a live
    `tcpdump`/firewall log confirming the same at the OS level (`operations/12_network_incidents.md`).
12. **RBAC denial beat.** Switch to `Restricted User`; attempt the same artifact-export action
    → `POLICY_DENIED` (`reference/01_error_codes.md`) shown clearly in the UI, logged to audit.

**Expected total wall-clock:** under 5 minutes end-to-end on PROFILE-B (REQ-PERF-001, DESIGN
LIMIT pending DEC-014 benchmark confirmation).

## Secondary scenarios

- **Coding sandbox demo** (`demo/06_coding_agent_demo.md`): agent writes and executes a small
  script inside the sandbox (`features/09_code_execution/`), demonstrating network-denied
  execution and resource limits.
- **Multimodal image demo** (`demo/07_multimodal_demo.md`): agent analyzes the synthetic
  equipment photo, with confidence and limitations stated explicitly per
  `features/12_multimodal/06_photo_analysis.md`.
- **Model fallback demo** (`demo/11_..` — mapped to `router/09_fallback_routing.md`): operator
  manually stops the primary model's runtime process mid-session; next request observably
  falls back per the router's deterministic fallback policy and surfaces `MODEL_UNAVAILABLE`
  → recovered, not a crash.

## Failure fallback during the live demo

If any step fails during the actual jury demo, `demo/13_failure_demo.md` defines the exact
recovery script (which pre-recorded state to fall back to, which step to skip, what to say) —
prepared in advance, not improvised.
