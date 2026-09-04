# Industrial Intelligence Overview

> These capabilities are built entirely on the core platform (`features/10_document_ingestion/`
> through `features/15_artifact_engine/`) — nothing here introduces new infrastructure; it
> defines domain-specific *workflows and expectations* on top of existing features.

## Scope

Industrial intelligence capabilities target the inspection-report / maintenance-record /
engineering-document use cases that motivate this project's evidence and classification
model (`workflows/01_inspection_report.md` is the canonical demo instance of this category).

## What's in this directory vs. what's a core feature

| Concern | Lives in |
|---|---|
| OCR, chunking, embedding, generic RAG | `features/10_document_ingestion/`, `13_knowledge_fabric/` (core, domain-agnostic) |
| "What does an inspection-report-specific finding look like, and how confident should the agent be" | This directory (domain-specific expectations layered on the core RAG/evidence pipeline) |
| Verifying an engineering calculation | `features/07_calculator_tool/` (core, deterministic) + `11_calculation_verification.md` (domain-specific: what "verified" means for an engineering claim) |

## V1 commitment

`02_inspection_reports.md` and `10_engineering_calculations.md`/`11_calculation_verification.md`
are demo-critical (`workflows/01_inspection_report.md`, `08_engineering_calculation.md`).
`08_p_and_id_intelligence.md` and `09_drawing_understanding.md` are V1-aspirational but not
demo-blocking — see `12_industrial_workflow_boundaries.md` for the explicit line and
`later/02_pid_analysis.md` / `later/04_drawing_intelligence.md` for the fuller V2 treatment.
