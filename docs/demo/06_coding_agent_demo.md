# Coding Agent Demo (Detailed Script)

> Detailed script for the secondary scenario referenced in `01_demo_overview.md`.

## Script

1. **(Say)** "Now a different kind of task — writing and running code, safely." **(Do)** Give
   the agent `03_demo_data.md`'s coding task prompt.
2. **(Say)** "This runs in an isolated sandbox with no network access." **(Do)** Show the
   Execution Graph (`ui/08_execution_graph_ui.md`) as the agent plans and executes steps.
3. **(Do)** If the first attempt has a test failure (can be seeded deliberately for the demo
   to show resilience), let the agent replan and self-correct — narrate this as
   `features/04_agent_kernel/10_replanning.md` in action.
4. **(Do)** Show the final passing test output and the generated code Artifact.

## Optional resilience beat

Deliberately seed a subtle bug in the task prompt's expected first attempt to *show* the
replanning loop working live, rather than hoping for a naturally-occurring failure — this
makes the demo's most interesting behavior (self-correction) reliably reproducible.
