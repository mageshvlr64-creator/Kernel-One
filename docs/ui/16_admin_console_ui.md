# Admin Console

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

User/role/model/policy management, system health

## User roles

Administrator (Operator for a subset)

## Key elements

- User table
- Model registry table
- Policy list
- System health summary

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: N/A (seed data always present). Loading: per-section skeletons. Error: per-section error banner, independent sections don't block each other. Permission-denied: 403 page for all non-Administrator/Operator roles.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
