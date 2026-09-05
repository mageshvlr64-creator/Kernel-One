# Risk Levels (Reference)

> Canonical definition of `low`/`medium`/`high` as used throughout `features/`,
> `reference/05_permission_matrix.md`, and `features/16_human_approval/`.

| Level | Definition | Example actions | Approval required? |
|---|---|---|---|
| `low` | Read-only or fully reversible, no data leaves its current scope | Chat, document read, search, calculator | No |
| `medium` | Writes data or has a limited, contained effect; reversible with effort | Document upload, artifact generation (non-export), most tool invocations | No, but subject to role/classification checks |
| `high` | Irreversible, exports data beyond its current boundary, or executes arbitrary code | Code execution, artifact export at CONFIDENTIAL+, destructive file operations, privileged config change | **Yes** — REQ-FUNC-003 |

## Assignment rule

A feature's risk level is assigned once, in its own `features/` file (see each file's
"Permission requirements" section), and referenced everywhere else (this table, the
permission matrix, the demo script) — never reassigned ad hoc per invocation.

## Escalation

An otherwise-`medium` action escalates to `high` if its target resource's classification is
`CONFIDENTIAL` or above (e.g. artifact export, per `workflows/07_report_generation.md`) — risk
level is a function of both the action type and the resource's classification, not the action
type alone.

## Why 3 tiers, not 4 (per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §17's suggestion)

The master prompt's example list includes a 4th, `critical` tier for actions like "execute
operational command." V1 of this system has no direct operational-control actions — it reads,
analyzes, and generates documents/reports; it does not write setpoints to equipment or issue
commands to industrial control systems (see `02_SCOPE_AND_NON_GOALS.md`). Every V1 action that
could plausibly be "critical" (destructive file operations, arbitrary code execution,
CONFIDENTIAL+ export) is already captured by `high` with mandatory approval. A 4th tier is
deferred to whenever direct operational-control actions are actually in scope (tracked as a
`later/` item), rather than added speculatively now with no action to populate it — see
DEC-021 in `20_DECISION_LOG.md`.
