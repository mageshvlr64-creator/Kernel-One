# Inspection Reports

> Domain-specific expectations for the inspection-report Q&A use case
> (`workflows/01_inspection_report.md`), built on `features/10_document_ingestion/`,
> `13_knowledge_fabric/`, and `14_evidence_and_provenance/`.

## What "a finding" means in this domain

A finding is a claim of the shape *{parameter, measured value, specification/threshold,
pass/fail, location reference}* — e.g. "Bolt torque on Flange B: 15% below spec, page 4."
The agent MUST attach an Evidence record (REQ-FUNC-005) to every one of these four elements
it states, not just the overall claim — a finding citing only the pass/fail verdict without
the underlying measured value and threshold is treated as an unsupported claim
(`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`).

## Confidence handling

If OCR confidence (`schemas/08_chunk_schema.md` `ocr_confidence` field) for the page containing
a finding is below 0.85 (CONFIG DEFAULT), the agent's answer explicitly flags the specific
number as "OCR confidence lower than usual — verify against the original document" rather than
stating it with the same certainty as a high-confidence extraction.

## Comparison across reports

`05_document_comparison.md` / `06_change_detection.md` extend this: comparing two inspection
reports of the same asset across time to surface newly-failing findings — implemented as two
separate retrieval+evidence passes (one per document) reconciled by the agent, not a special
retrieval mode.
