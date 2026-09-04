# Model Selector / Status Panel

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Choose/inspect available models and their health

## User roles

All roles (selector limited by role)

## Key elements

- Model list with capability badges
- Health indicator per model
- VRAM/resource usage (Operator/Administrator only)

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'No models configured' (should never occur in a valid deployment — flagged as a configuration error state, not a normal empty state). Loading: health check spinner per model. Error: model row shows MODEL_UNAVAILABLE badge. Permission-denied: resource usage numbers hidden from Analyst/Restricted User.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
