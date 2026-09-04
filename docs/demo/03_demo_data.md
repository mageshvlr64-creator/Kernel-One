# Demo Data

> The exact synthetic dataset used across every demo scenario — never real customer or
> proprietary data (per the constraint also applied to `benchmarks/02_benchmark_dataset.md`).

## Primary document

"Synthetic Industrial Inspection Report" — a 10-page PDF:
- Pages 1-3: native text (cover page, summary, methodology).
- Pages 4-7: scanned images of a filled inspection form (deliberately included to exercise
  OCR, REQ-AI-002) containing a small number of clearly identifiable findings, e.g. "Bolt
  torque on Flange B: measured 42 Nm, spec 50 Nm, 16% below specification."
- Pages 8-10: native text (recommendations, sign-off).

## Secondary assets

- One synthetic equipment photograph (for `07_multimodal_demo.md`).
- One small XLSX workbook with a handful of formulas (for the spreadsheet-adjacent beat, if
  included).
- One small Python coding task prompt (for `06_coding_agent_demo.md`) with a deterministic
  expected output, so success/failure is unambiguous during a live demo.

## Why findings are deterministic

Every finding in the primary document has a known, fixed expected answer — this is what makes
`TEST-E2E-001` and the live demo's success criterion objective rather than subjective ("did
the agent find the right page and the right number" is checkable, "did the agent give a good
answer" is not, for live-demo purposes).
