# Control Flow

> Authorization and decision-making flow, complementing `07_data_flow.md`'s data movement view.

## Every state-changing request's control flow

```
Request -> API (authn) -> Policy Engine (authz decision) -> [DENIED: return error, audit, stop]
                                                          -> [ALLOWED: proceed to owning service]
Owning service -> [risk=high? -> Human Approval gate -> wait for decision] -> execute -> Audit
```

## Agent planning control flow

```
Task created -> Agent Kernel requests a Plan from the Model Router/Inference Gateway
  -> Plan validated (features/04_agent_kernel/05_plan_validation.md)
  -> [INVALID: replan or fail] -> [VALID: Step Scheduler executes steps in dependency order]
  -> each step's tool call re-enters the "every state-changing request" control flow above
     (a plan step does not inherit blanket authorization from the plan having been validated)
```

## Key architectural point

Plan validation checks *structure* (valid tool IDs, valid dependency graph); it does NOT grant
authorization for any step — each step is authorized independently at execution time, which is
why `security/07_tool_abuse.md`'s mitigation ("no chained privilege") is architecturally true,
not just a policy statement.
