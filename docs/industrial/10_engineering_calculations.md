# Engineering Calculations

> Domain-specific calculation patterns built on `features/07_calculator_tool/` — this file
> defines what kinds of calculations this domain needs; the Calculator Tool itself is
> domain-agnostic.

## Common calculation classes in this domain

- **Tolerance/spec checking:** `measured_value` vs. `{min, max}` or `{nominal, tolerance}` —
  a boolean pass/fail plus the percentage deviation, always computed via the Calculator Tool,
  never asserted by the model from "reading" the numbers.
- **Unit conversion:** engineering documents mix unit systems (metric/imperial); any
  cross-unit comparison goes through an explicit, auditable conversion step
  (`features/07_calculator_tool/03_units.md`) rather than an implicit mental conversion by the
  model.
- **Aggregate statistics across multiple findings:** e.g. "average deviation across all bolt
  torque findings in this report" — computed by the Calculator Tool over the actual retrieved
  values, not estimated.

## Rule

Every numeric claim in an engineering-domain answer that could be computed IS computed via the
Calculator Tool and cites the tool's ToolInvocation as part of its Evidence — a numeric claim
the model states without an underlying ToolInvocation is treated identically to any other
unsupported claim (REQ-FUNC-005's spirit extended to numeric claims specifically).
