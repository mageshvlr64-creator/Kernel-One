# PaddleOCR Integration

> OCR engine for `features/11_ocr/` (chosen for reasonable CPU-only accuracy without requiring
> a GPU, matching REQ-AI-002's fallback requirement).

## Contract

Adapter wraps PaddleOCR's Python API, returning per-region text + bounding box + confidence,
normalized to `schemas/08_chunk_schema.md`'s `bbox`/`ocr_confidence` fields.

## Why this specific engine

Chosen for balancing CPU-only accuracy against `performance/10_document_processing_performance.md`'s
per-page latency target — an alternative OCR engine could be substituted behind the same
adapter interface if a future benchmark (`later/11_advanced_model_benchmarking.md`-adjacent
effort) shows a better tradeoff, without requiring changes outside this adapter.

## Failure modes

See `failures/22_ocr_failures.md`.
