# Feature 07 — Artifact Engine

## Purpose
Turns verified model output into a real downloadable deliverable (DOCX approval note, XLSX summary, PDF report) — this is what makes the demo end with something a judge can actually open, not just chat text.

## How to build

1. **Templates, not free-form generation** — define 1-2 fixed DOCX templates (e.g. "Inspection Approval Note": header, findings table, recommendation, signature block) using `python-docx`. Have the LLM's verified output fill named fields/sections of the template rather than generating a whole document from scratch — this dramatically improves reliability and formatting consistency for a live demo.
2. **DOCX generation** — `python-docx`: create headings, a findings table (`doc.add_table`), and paragraph text from the model's structured output (have the generation step return JSON with fields like `findings: []`, `recommendation: str`, not raw prose, so the template filler doesn't need to parse free text).
3. **XLSX generation** (stretch, Day 13 slot) — `openpyxl`: write a summary sheet from structured data, useful for the "analyze spreadsheets" capability if time allows.
4. **PDF generation** (optional third format) — `reportlab` or `fpdf2` if you want a PDF option beyond DOCX; not required for V1 if time is short — DOCX alone satisfies the demo.
5. **File serving** — write the generated file to a scoped temp/output directory, return a download URL/endpoint from the API, and make sure the artifact-generation step is itself a visible execution-graph step (`✓ DOCX generated`) as shown in your source doc's example.
6. **Provenance stamp** — embed a small footer/metadata note in the generated doc referencing the `task_id` so it's traceable back to its audit log entry — a nice, cheap touch that reinforces "auditable."

## Data/API contract

```json
// input to artifact engine (structured, not free text)
{"template": "inspection_approval_note", "fields": {
  "findings": ["...", "..."],
  "recommendation": "...",
  "task_id": "uuid"
}}
→
{"file_path": "/outputs/task_uuid.docx", "status": "generated"}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Generated DOCX is malformed/won't open | Template code path hits an edge case (empty findings list, special characters) | Test the template with empty, single-item, and multi-item findings lists, and with text containing quotes/newlines before demo day |
| Model output doesn't match the expected structured schema, breaking the template filler | Free-text generation used instead of constrained structured output | Have the generation prompt explicitly request JSON matching the template's field schema; validate and fall back to a safe default (e.g. "recommendation: see findings above") rather than crashing if a field is missing |
| Download link works in dev but 404s in the demo build | Output directory path hardcoded to dev machine, or not created on the demo machine | Use a relative/configurable output path, and verify the full upload→generate→download flow on the actual demo hardware, not just localhost dev |
| Artifact generation step silently fails and the execution graph just... stops | Exception in `python-docx` calls not caught | Wrap generation in try/except like every other kernel step (Feature 02) and surface a clear error state, not a hang |
| Sensitive info leaks into a generated file that shouldn't be there | No filtering between raw retrieved context and what's written into the final artifact | Only pass explicitly verified/approved fields (post human-approval, Feature 09) into the artifact — never the raw RAG context dump |

## Definition of Done
Completing the demo flow's "generate approval note" step produces a real, correctly formatted .docx file, downloadable through the UI, containing the model's findings and a recommendation, traceable to its `task_id`.
