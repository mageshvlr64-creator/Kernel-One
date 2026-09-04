# Evidence / Citation Panel

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Show citations for an agent answer and let the user jump to the source

## User roles

All roles with document read access

## Key elements

- Citation list
- Source excerpt preview
- Page jump link

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'No evidence attached to this answer' — flagged distinctly since REQ-FUNC-005 means this should be rare/investigatable. Loading: skeleton citation cards. Error: 'Source unavailable' if document was deleted after answer was generated. Permission-denied: citation hidden (not just source) if caller's clearance dropped below the document's classification since the answer was generated.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
