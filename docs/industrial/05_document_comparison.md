# Document Comparison

> Structured diff between two documents (two versions of the same document, or two related
> documents), used by `02_inspection_reports.md` and `workflows/06_document_comparison.md`.

## Approach

1. Retrieve relevant chunks from Document A and Document B independently
   (`features/13_knowledge_fabric/`), each with its own classification/permission filter
   applied (a comparison never bypasses REQ-FUNC-004 by treating the pair as a single merged
   context).
2. Align chunks by semantic similarity and, where available, matching page/section structure.
3. Generate a structured diff: `{added findings, removed findings, changed findings}`, each
   with Evidence from its respective source document.

## What counts as "changed" vs. "added/removed"

A finding is "changed" if the same parameter/location is present in both documents with a
different measured value or verdict; "added" if present only in the later document; "removed"
if present only in the earlier document. This is a deterministic rule applied to the retrieved
findings, not a subjective judgment left to the model — see `06_change_detection.md` for the
matching heuristic.
