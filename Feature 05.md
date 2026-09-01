# Feature 05 — Tool Execution Gateway

## Purpose
The enforcement point of the "sovereign" claim: the LLM never touches a tool directly. It proposes a call; the gateway validates it against RBAC/policy and only then executes it. Without this, "permission-aware" is just a slide, not a real property of the system.

## How to build

1. **Tool interface** — every tool (sandbox exec, calculator, filesystem read within an allowed dir, artifact generator) implements the same shape: `name, description, input_schema (JSON schema), security_class, handler(args) -> result`.
2. **Tool registry** — a simple dict/list of registered tools, analogous to the Model Registry (Feature 01).
3. **LLM tool-call protocol** — prompt the model to emit a structured request when it wants to use a tool, e.g. a fenced JSON block: `{"tool": "sandbox_exec", "args": {"code": "..."}}`. Parse this from the model output — don't give the model direct function-calling access to your process; treat its output as untrusted text to be parsed and validated, same as user input.
4. **Validation before execution** — the gateway checks: (a) does this tool exist in the registry, (b) do the args match the schema, (c) does the requesting user's RBAC role (Feature 12) permit this tool's `security_class`. Reject with a clear reason if any check fails.
5. **Execute and return structured result** — the handler runs, result (or error) is returned to the kernel as the step's `detail`, and logged to audit (Feature 10) with the exact args and result — this is what makes the audit trail meaningful, not just "a tool ran."

## Data/API contract

```json
// model's proposed call (untrusted, parsed from generation)
{"tool": "sandbox_exec", "args": {"code": "print(2+2)"}}
// gateway's validated result
{"tool": "sandbox_exec", "status": "allowed", "result": "4", "duration_ms": 120}
// or
{"tool": "sandbox_exec", "status": "denied", "reason": "role 'viewer' lacks 'code_execution' permission"}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Model's tool-call output isn't valid JSON / doesn't match schema | Small local models are less reliable at structured output than large ones | Use a strict, simple output format (a single fenced JSON block with few fields) and a regex/parse-with-fallback; on parse failure, treat as "no tool call" and surface a normal text answer rather than crashing the task |
| A denied tool call isn't logged, only allowed ones are | Logging placed after the permission check instead of wrapping both branches | Log every proposed call and its allow/deny outcome, not just successful executions — the denial is itself the proof RBAC works |
| Tool executes with unvalidated/unsanitized args (e.g. path traversal in a filesystem tool) | Schema check exists but doesn't constrain value ranges, only types | Validate value constraints too (e.g. filesystem tool args must resolve inside an explicit allowed directory; reject `..` path segments) |
| Gateway becomes a second place tools get called from (kernel calls handler directly somewhere) | Convenience shortcut added under time pressure | Enforce one code path: the kernel/UI never imports a tool handler directly, only ever goes through the gateway's `execute(tool_name, args, user)` function |
| Long-running tool call blocks other users/tasks | Synchronous execution in the main event loop | Same as Feature 02 — run tool handlers via `asyncio.to_thread` or a subprocess with a timeout |

## Definition of Done
A tool call proposed by the model for an allowed role executes and logs correctly; the identical call for a restricted role is denied, logged, and surfaced to the user with a clear reason — demonstrable live for Feature 12's RBAC part of the demo.
