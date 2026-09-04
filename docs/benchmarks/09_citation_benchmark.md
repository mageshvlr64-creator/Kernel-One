# Citation Benchmark

> The most safety-relevant benchmark for this product's core value proposition — a narrower,
> citation-specific slice of `04_document_benchmark.md`.

## Method

For a set of document-grounded answers, verify: every citation resolves to a real chunk, the
cited chunk's content actually supports the specific claim it's attached to (not just
topically related), and no claim in the answer lacks a citation at all (the direct check
REQ-FUNC-005 requires in production via `features/14_evidence_and_provenance/09_unsupported_claim_detection.md`
— this benchmark evaluates how well a *candidate* model performs at this before it's pinned).

## Scoring

Precision (of cited claims, how many are actually supported) and recall (of citable claims,
how many did the model actually cite) — both matter; a model that cites nothing scores zero
recall even with perfect precision.
