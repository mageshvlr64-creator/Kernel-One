# Tool Use Benchmark

> Evaluates tool-calling reliability — does the model select the correct tool, with correctly
> formatted arguments, for a given task.

## Method

Fixed scenarios with a known-correct tool sequence; scored on: correct tool selection, correct
argument formatting (schema-valid on the first attempt, per `schemas/05_tool_call_schema.md`),
and correct handling of a tool's failure result (does the model appropriately replan rather
than repeating the identical failing call).

## Relationship to REQ-AI-001

This benchmark is what a model needs to pass reasonably well to be viable for the
`tool_calling` capability tag (`reference/08_model_capability_matrix.md`) — a model without
this capability cannot serve as the Agent Kernel's planning model at all, per that matrix's
"no fallback" note.
