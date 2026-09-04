# Change Detection

> The specific matching heuristic `05_document_comparison.md` uses to decide whether two
> findings across documents refer to the "same" underlying item.

## Matching heuristic

Two findings match if they share the same normalized `parameter` name (case/whitespace
normalized, common synonym list applied — e.g. "torque" and "tightening force" treated as
equivalent only if an explicit synonym mapping exists, never inferred by the model at
comparison time) AND the same `location reference` (e.g. "Flange B") if present in both.

## Ambiguous matches

If a finding in Document B has no clear match in Document A (different parameter name, no
synonym mapping, but plausibly related), it is reported as **added**, not silently matched to
the nearest candidate — a false match that hides a genuinely new finding is a worse failure
mode than an extra "added" entry a human reviewer can dismiss.

## Confidence in the diff

Each diff entry carries the confidence of its underlying retrieval (`domain/13_evidence_model.md`
`confidence` field, inherited from each side's Evidence) — a low-confidence match is flagged
distinctly in the UI rather than presented with the same certainty as a high-confidence one.
