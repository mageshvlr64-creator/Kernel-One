# Policy Testing

> Covers `features/21_policy_engine/` and `features/20_data_classification/` specifically —
> operator-configured Policy rows layered on top of the base role matrix.

## Required tests

- A Policy row can further restrict (deny) beyond the base role matrix, never grant beyond it
  (`domain/16_policy_model.md`'s composition rule) — a test asserts a Policy attempting to
  grant an action the role matrix denies has no effect.
- Policy precedence (`features/21_policy_engine/04_policy_precedence.md`): when multiple
  Policy rows apply, the lower-`priority`-number rule is evaluated first, and a `deny`
  short-circuits regardless of a later, higher-priority `allow`.
- `TEST-CLASS-001`: classification inheritance produces the correct computed classification
  for a derived Artifact.
