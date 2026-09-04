# Document Pipeline Testing

> Covers `features/10_document_ingestion/` end-to-end: upload → validation → extraction →
> (OCR) → indexing.

## Required tests

- Native-text PDF: full state progression to `READY`, chunks correctly extracted with page
  numbers and bounding boxes.
- Scanned PDF: correctly routed through OCR (REQ-AI-002), resulting chunks carry
  `ocr_confidence`.
- Malformed/corrupted PDF: fails per `failures/21_pdf_failures.md` with `INVALID_REQUEST`, not
  a crash.
- Oversized file: rejected before any processing begins (`MAX_UPLOAD_SIZE_BYTES` check).
