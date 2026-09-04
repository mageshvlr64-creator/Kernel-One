# Execution Graph Demo

> A focused walkthrough of `ui/08_execution_graph_ui.md`, usable as a standalone beat if a
> technical audience wants to see "under the hood" beyond the primary scenario.

## Script

1. **(Do)** Open the Execution Graph for any completed task from an earlier demo beat.
2. **(Say)** "Every node here is independently authorized and audited — nothing is trusted
   just because it's part of an approved plan." **(Do)** Click a node to show its
   ToolInvocation detail (state, input, output).
3. **(Do)** Point out a step with a dependency edge, explaining the Step Scheduler
   (`features/04_agent_kernel/07_step_scheduler.md`) executed it only after its dependency
   completed.
