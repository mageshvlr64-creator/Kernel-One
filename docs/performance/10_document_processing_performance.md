# Document Processing Performance

> Budgets specific to `features/10_document_ingestion/` and `features/11_ocr/`.

| Metric | Target | Provenance |
|---|---|---|
| Native-text PDF parsing | < 1s per page (p95) | CONFIG DEFAULT |
| Scanned page OCR (CPU-only, PROFILE-A/B) | < 3s per page (p95) | DESIGN LIMIT — this is the single slowest step in the demo pipeline and the primary driver of REQ-PERF-001's overall 5-minute target |
| Chunking + embedding, per document | < 2s per 10 pages (p95) | CONFIG DEFAULT |
| End-to-end ingestion (upload to READY), 10-page mixed document | < 60s (p95) | DESIGN LIMIT, rolls up the above |

## Why OCR dominates this budget

A 10-page scanned document at 3s/page is 30s of the ~60s end-to-end target — this is why
`06_cpu_only_demo.md` explicitly does not carry the same performance guarantee, and why a GPU
host for the demo (PROFILE-B) matters less for OCR specifically (OCR here is assumed CPU-bound
regardless of GPU presence, per `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) than for
inference — OCR acceleration is a possible future optimization, not assumed in V1's budget.
