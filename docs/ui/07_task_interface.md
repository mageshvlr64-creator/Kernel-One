# Task Detail

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

View a single Task's state, plan, and history

## User roles

Task owner, Administrator, Operator, SecurityOfficer (workspace)

## Key elements

- State badge
- Plan step list
- Cancel button (if cancellable)

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: N/A (task always has at least CREATED state). Loading: state badge pulses. Error: failed step highlighted red with error code. Permission-denied: 403 page if caller isn't owner/workspace-privileged role.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
