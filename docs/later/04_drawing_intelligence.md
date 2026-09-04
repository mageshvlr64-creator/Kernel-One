# Drawing Intelligence (V2+)

> Structured successor to `industrial/09_drawing_understanding.md`'s V1-aspirational
> description-only capability.

## What this would add over V1

Calculator-grade dimension/tolerance extraction from engineering drawings — i.e., a value read
from a drawing would carry the same verification status as a value read from a spec table
(`industrial/07_engineering_documents.md`), rather than the current "unverified, confirm
against source" caveat.

## Concrete technical prerequisite

This requires either (a) a specialized drawing-dimension-extraction model/pipeline (distinct
from general vision-language description) or (b) a much stronger general vision-language model
with demonstrated, benchmarked accuracy on dimension reading specifically — general "can this
model describe an image reasonably" capability (which is what V1's vision slot provides,
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) is not sufficient evidence for (b).

## Evaluation bar before promotion out of "later"

A benchmark showing dimension-reading accuracy within an explicitly stated tolerance (e.g.
"correct to the stated precision in 95% of a labeled test set of N drawings") must exist and
be reviewed before this capability is promoted from `later/` to `industrial/` V1-aspirational
status, let alone V1-committed.
