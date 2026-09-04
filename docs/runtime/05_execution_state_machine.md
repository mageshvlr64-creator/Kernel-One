# Execution State Machine

> Pointer file. "Execution" in this codebase refers to a `ToolInvocation`'s lifecycle within
> a task's execution phase. The canonical machine is defined once, in
> `docs/runtime/_state_machines_canonical.md#toolinvocation` — see that file for the full
> state table (CREATED → AUTHORIZED → RUNNING → SUCCEEDED/FAILED/TIMEOUT/CANCELLED), owners,
> and audit events. This file does not redefine it.
