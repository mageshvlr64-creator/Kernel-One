# Router Scoring

> How the dimensions from `01_benchmark_overview.md` combine into
> `features/02_model_router/04_model_scoring.md`'s actual scoring function — this file is the
> bridge between offline benchmark results and the live router's decision logic.

## Scoring inputs (V1, informal)

In V1, the router's scoring is primarily capability-tag matching + hardware fit + policy
compliance (`features/02_model_router/`'s existing files) — benchmark scores inform which
model is *registered* for a capability slot (a human/DEC-013 decision), not a live input the
router itself weighs at request time.

## V2 evolution

`later/11_advanced_model_benchmarking.md`'s automated harness would feed benchmark scores
directly into the router's live scoring function (e.g. preferring a higher-citation-accuracy
model specifically for document-Q&A-classified requests) — this is explicitly a V2
capability, not attempted in V1's simpler capability-tag-based routing.
