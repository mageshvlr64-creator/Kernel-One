# Engineering Calculation Engine (V2+)

> Structured successor to `industrial/10_engineering_calculations.md`'s V1 pattern (ad hoc
> Calculator Tool invocations per finding).

## What this would add over V1

A formula/standards library (e.g. specific torque-spec formulas per bolt class and standard)
that the agent selects from explicitly, rather than the model choosing an ad hoc formula per
question. This directly addresses the gap named in
`industrial/11_calculation_verification.md`: "the system does not verify formula selection" —
a proper engine would make formula selection itself an auditable, versioned choice
(`{standard_id, formula_id}` recorded per calculation, not just the numeric inputs/output).

## Why this is a real engineering effort, not a config addition

Each formula/standard entry needs: the formula itself, its applicability conditions (e.g.
material, size range), a citation to the actual standard document, and a review/approval
process for adding new entries (this is exactly the kind of "policy" data that should go
through the same rigor as `domain/16_policy_model.md`, not be hardcoded).

## Prerequisite

A named domain expert or standards body input is required to seed the initial formula library
correctly — this is explicitly not something to auto-generate from model output, since a
wrong formula silently presented as verified is worse than no automation at all.
