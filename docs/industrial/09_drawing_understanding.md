# Drawing Understanding

> General engineering-drawing (non-P&ID) visual understanding — **V1-aspirational**, same
> status as `08_p_and_id_intelligence.md`. See `later/04_drawing_intelligence.md` for the V2
> treatment.

## V1 scope

Same constraint as P&ID: `features/12_multimodal/` can describe a drawing in general visual
terms via a vision-capable model, explicitly caveated as a description rather than a
dimension/tolerance extraction. Numeric dimensions read off a drawing by the vision model are
treated as **unverified OCR-adjacent extraction**, not a calculator-verified value
(`features/07_calculator_tool/05_deterministic_verification.md` applies only to values the
Calculator Tool has actually computed or checked, not to values a vision model merely read off
an image).

## Required user-facing caveat

Any dimension or tolerance value stated by the agent from a drawing image includes: "read from
the drawing image, not independently verified — confirm against the source before acting on
this number."
