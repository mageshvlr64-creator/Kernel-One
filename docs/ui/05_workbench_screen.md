# Workbench (Dashboard)

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Landing screen after login

## User roles

Analyst, Administrator, Restricted User

## Key elements

- Recent tasks list
- New task input
- Model status indicator

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'No tasks yet — start one below.' Loading: skeleton rows. Error: 'Couldn't load your tasks — retry.' Permission-denied: N/A (always accessible once authenticated).

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
