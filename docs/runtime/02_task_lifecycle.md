# Task Lifecycle

> Narrative walkthrough of the Task state machine (`_state_machines_canonical.md#task`) — the
> readable version; that file is the formal transition table.

## Walkthrough

A Task is `CREATED` the moment a user's message or API call requests work. The Agent Kernel
immediately begins `PLANNING` — generating a Plan via the Model Router/Inference Gateway. If
any planned step is `risk=high` (`reference/03_risk_levels.md`), the Task pauses at
`WAITING_APPROVAL` before a single step executes. Once cleared (or if nothing required
approval), the Task enters `EXECUTING`, running Plan steps via the Step Scheduler
(`features/04_agent_kernel/07_step_scheduler.md`) in dependency order. A step needing more
information from the user moves the Task to `WAITING_INPUT`; receiving that input returns it
to `PLANNING` (the plan may be revised given the new information). Successful completion of
all steps moves the Task to `COMPLETED`; an unrecoverable failure at any stage moves it to
`FAILED`; explicit user cancellation moves it to `CANCELLED` from any non-terminal state.

## Why `WAITING_INPUT` returns to `PLANNING`, not directly to `EXECUTING`

New user input can change which steps are still relevant — re-planning (not just resuming) is
the safer default, consistent with `features/04_agent_kernel/10_replanning.md`'s general
philosophy of never blindly continuing a stale plan.
