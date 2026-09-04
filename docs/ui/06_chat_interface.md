# Chat / Conversation

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Send messages, view agent responses with inline citations

## User roles

All roles

## Key elements

- Message input
- Send button
- Model selector (if role permits override)

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: 'Ask a question to get started.' Loading: typing indicator during model generation. Error: inline error bubble showing the error registry message. Permission-denied: model selector hidden for Restricted User.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
