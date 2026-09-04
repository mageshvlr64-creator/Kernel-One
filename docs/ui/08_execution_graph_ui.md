# Execution Graph

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Visualize plan steps and dependencies as a graph

## User roles

Task owner, Administrator, Operator

## Key elements

- Step nodes colored by state
- Dependency edges
- Click-through to step detail

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'Plan not yet generated.' Loading: nodes appear as planning streams in. Error: failed node shown with error tooltip. Permission-denied: same as Task Detail.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
