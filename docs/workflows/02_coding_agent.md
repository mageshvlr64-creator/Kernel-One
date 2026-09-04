# Autonomous Coding Task

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

REQ-FUNC-002, REQ-SEC-002

## Steps

1. User asks agent to write and test a small script
2. Agent kernel generates a Plan (schemas/04_execution_schema.md) with code_execution.run steps
3. Sandbox executes each step with network denied (features/09_code_execution/06_network_isolation.md)
4. Tool output captured and attached to the AgentRun; on test failure, agent replans (features/04_agent_kernel/10_replanning.md) up to AGENT_MAX_REPLANS
5. Final code + test output returned as an Artifact (type=code)

## Notes

See demo/06_coding_agent_demo.md for the exact scripted version of this workflow.
