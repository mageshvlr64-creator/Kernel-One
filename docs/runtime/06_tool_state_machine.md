# Tool State Machine

> Pointer file — identical scope to `05_execution_state_machine.md`. The canonical
> `ToolInvocation` machine is defined once in
> `docs/runtime/_state_machines_canonical.md#toolinvocation`. A registered `Tool`'s
> enable/disable status (distinct from a single invocation's lifecycle) is not a multi-state
> machine — it is a boolean flag on the Tool definition in
> `docs/features/05_tool_gateway/02_tool_registration.md`, which references these shared
> conventions rather than defining a separate state machine.
