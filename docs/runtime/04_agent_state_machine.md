# Agent / Task State Machine

> Pointer file. The canonical Task state machine (states, transitions, owners, side effects,
> audit events) lives in `docs/runtime/_state_machines_canonical.md#task`. This file exists
> only so the filename matches the documentation index; it does not redefine the machine.

See `docs/runtime/_state_machines_canonical.md` for:
- The Task state table (CREATED → PLANNING → WAITING_APPROVAL → EXECUTING → WAITING_INPUT →
  COMPLETED/FAILED/CANCELLED)
- Shared state-machine conventions (illegal transition handling, audit requirements)
- The machine-readable JSON representation used by the runtime's transition guard
