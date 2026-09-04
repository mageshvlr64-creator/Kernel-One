# PyMuPDF Integration

> PDF parsing library for `features/10_document_ingestion/04_native_pdf_parsing.md` (text
> layer extraction, page rendering for OCR handoff, table/image extraction).

## Contract

Adapter extracts: page text (with bounding boxes for citation coordinates,
`domain/13_evidence_model.md`), page images (for pages requiring OCR), and embedded tables
where detectable.

## Security note

PDF parsing is a documented attack surface (`security/17_malicious_documents.md`) — this
library is kept current via the dependency-scanning gate (`security/20_dependency_security.md`)
specifically because PDF parser vulnerabilities are a known, recurring category of security
issue industry-wide.

## Failure modes

See `failures/21_pdf_failures.md`.
