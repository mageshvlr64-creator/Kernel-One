# Industrial Workflow Boundaries

> The explicit V1-committed vs. V1-aspirational vs. V2 line for every capability in this
> directory — referenced by `01_industrial_intelligence_overview.md` rather than restated
> per-file.

## V1-committed (demo-critical, fully specified and tested)

| Capability | File | Test |
|---|---|---|
| Inspection report Q&A with evidence | `02_inspection_reports.md` | `TEST-E2E-001` |
| Engineering calculations (Calculator-Tool-backed) | `10_engineering_calculations.md` | covered under `features/07_calculator_tool/` test requirements |
| Calculation verification framing | `11_calculation_verification.md` | manual review of demo answer copy |

## V1-aspirational (implemented if time permits, not demo-blocking, explicitly caveated to the user when present)

| Capability | File | Caveat required |
|---|---|---|
| P&ID visual description | `08_p_and_id_intelligence.md` | "description, not structured extraction" |
| Drawing dimension reading | `09_drawing_understanding.md` | "unverified, confirm against source" |
| Document comparison / change detection | `05_document_comparison.md`, `06_change_detection.md` | confidence shown per diff entry |

## V2 (not attempted in V1 under any circumstance)

| Capability | Tracked in |
|---|---|
| Structured P&ID symbol/tag extraction with a rule engine | `later/02_pid_analysis.md` |
| Dimension/tolerance extraction with calculator-grade verification from drawings | `later/04_drawing_intelligence.md` |
| Full engineering calculation engine (formula library, standards lookup) | `later/03_engineering_calculation_engine.md` |

## Rule for anyone extending this directory

A new industrial capability is added to the V1-committed table only if it has a REQ ID
(`03_REQUIREMENTS.md`) and a test ID — "seemed useful to add" is not sufficient justification
to move something out of V1-aspirational or V2.
