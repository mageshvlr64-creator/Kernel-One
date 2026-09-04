# Coding Benchmark

> Evaluates code generation and self-correction quality for the `coding` capability slot.

## Method

A fixed set of small coding tasks (e.g. "write a function that does X, with tests") run
through the full Agent Kernel + Code Execution pipeline; scored on: does the generated code
run, do the tests pass, and does the agent successfully self-correct on a first-attempt test
failure (exercising `features/04_agent_kernel/10_replanning.md`) within
`AGENT_MAX_REPLANS`.

## Note

This benchmark exercises the same pipeline as `demo/06_coding_agent_demo.md` — it is
effectively that demo scenario run across multiple candidate models for comparison, rather
than a separate isolated code-quality benchmark.
