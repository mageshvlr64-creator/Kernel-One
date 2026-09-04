# Execution Lifecycle

> Narrative walkthrough of the ToolInvocation state machine
> (`_state_machines_canonical.md#toolinvocation`).

## Walkthrough

A ToolInvocation is `CREATED` the instant the Agent Kernel's Step Scheduler decides to invoke
a tool for a Plan step. The Tool Gateway immediately evaluates authorization
(`features/05_tool_gateway/04_tool_permissions.md`); success moves it to `AUTHORIZED`, failure
moves it directly to `FAILED` with `TOOL_NOT_ALLOWED` — no tool ever executes without first
passing through `AUTHORIZED`. Once authorized, the tool's own implementation runs
(`RUNNING`), ending in `SUCCEEDED`, `FAILED` (the tool itself reported an error), `TIMEOUT`
(exceeded its operation class's timeout, `11_retry_policy.md`), or `CANCELLED` (the parent
Task was cancelled mid-invocation).

## Relationship to the Task lifecycle

A ToolInvocation's terminal state feeds back into the owning AgentRun's step-completion
tracking, which the Step Scheduler uses to decide whether to proceed to the next step, trigger
a replan, or complete the Task — the two state machines are independent but tightly coupled in
this one direction (ToolInvocation outcome → AgentRun progress), never the reverse.
