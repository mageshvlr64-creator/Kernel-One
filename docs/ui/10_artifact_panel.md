# Artifact Panel

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

List and download generated artifacts for a task

## User roles

All roles with Artifact:read

## Key elements

- Artifact list with type icons
- Download button
- Approval status badge

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'No artifacts generated yet.' Loading: spinner on the specific artifact being generated. Error: 'Generation failed' with error code. Permission-denied: download button replaced with 'Approval required' if state requires it and caller isn't the approver.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
