# Engineering Documents

> Domain-specific handling for engineering drawings, specs, and datasheets — the document
> types feeding `08_p_and_id_intelligence.md`, `09_drawing_understanding.md`, and
> `10_engineering_calculations.md`.

## Ingestion notes specific to this document type

Engineering documents frequently mix dense tabular data (spec tables), diagrams, and small
annotation text — `features/10_document_ingestion/08_table_extraction.md` and
`09_image_extraction.md` are both exercised more heavily here than for prose-only documents
like general reports. Table extraction accuracy is the primary quality gate for this document
type — a mis-parsed spec table (e.g. a shifted column) silently produces wrong "spec" values
in every downstream finding, so `10_engineering_calculations.md` treats table-derived values
as **lower-confidence by default** than directly-stated prose values, pending explicit
verification (`11_calculation_verification.md`).

## V1 scope note

Full diagram/schematic understanding (P&ID symbol recognition, drawing dimension extraction)
is V1-aspirational, not V1-committed — see `12_industrial_workflow_boundaries.md`.
