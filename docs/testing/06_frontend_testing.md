# Frontend Testing

> Covers `docs/ui/` — component rendering, state-based UI logic (loading/empty/error/
> permission-denied states per `ui/17..20_*_states.md`), and accessibility.

## Required per screen

- Renders correctly for each documented state (`ui/17_error_states.md` through
  `20_permission_denied_states.md`).
- Permission-gated controls render per `reference/05_permission_matrix.md` for each role
  (hidden vs. disabled-with-tooltip vs. fully enabled, per `ui/20_permission_denied_states.md`'s
  distinction).
- Accessibility check (axe-core or equivalent) per `ui/21_accessibility.md`.

## Out of scope here

Actual API integration correctness is covered by `05_api_testing.md`/`13_tool_testing.md` etc.
— frontend tests mock the API layer to test UI behavior in isolation.
