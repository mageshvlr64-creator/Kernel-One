# Calculation Verification

> What "verified" means for an engineering calculation in this system, and — critically —
> what it does NOT mean, to avoid the automated-assurance overclaiming risk noted in
> `04_sop_compliance.md`.

## What IS verified

- **Arithmetic correctness:** the Calculator Tool's computation is deterministic and
  independently re-checkable — this is genuinely verified, the same way any calculator's
  arithmetic is trustworthy.
- **Input traceability:** every input to a calculation has an Evidence record showing where
  the input value came from (REQ-FUNC-005) — so a wrong *answer* can always be traced to
  either a wrong *input value* (an extraction/OCR problem, distinct from a calculation
  problem) or a wrong *formula*.

## What is NOT verified

- **Whether the correct formula was chosen** for the engineering context — the system verifies
  that a stated formula was computed correctly, not that the formula itself is the
  domain-appropriate one for this specific equipment/standard. This requires domain expert
  review; the system does not claim to replace that review.
- **Whether the extracted input values are themselves correct** — an OCR misread threshold
  value, if not caught, will be "correctly" calculated against a wrong number. Low-confidence
  extractions (`02_inspection_reports.md`) are flagged precisely so a human can catch this
  class of error before acting on the result.

## Required framing

Any engineering-calculation answer states its verification scope explicitly: "arithmetic
verified; formula selection and input values require human confirmation" — or an equivalent,
proportionate to the specific calculation's risk level.
