# Tool Matrix (Reference)

> Canonical list of every registered Tool, its risk level, and its owning feature group.

| Tool ID | Risk level | Owning feature | Network required? |
|---|---|---|---|
| `filesystem.read` | `low` | `features/06_filesystem_tool/` | No |
| `filesystem.write` | `medium` | `features/06_filesystem_tool/` | No |
| `calculator.evaluate` | `low` | `features/07_calculator_tool/` | No |
| `database.query` (read) | `medium` | `features/08_database_tool/` | No |
| `database.query` (write) | `high` | `features/08_database_tool/` | No |
| `code_execution.run` | `high` | `features/09_code_execution/` | No (explicitly denied at the container layer, DEC-005) |
| `search.retrieve` | `low` | `features/13_knowledge_fabric/` | No |
| `artifact.generate` | `medium` | `features/15_artifact_engine/` | No |
| `artifact.export` | `high` (escalates further at CONFIDENTIAL+, `03_risk_levels.md`) | `features/15_artifact_engine/` | No |

## Rule

Every tool listed here must have a matching entry in `features/05_tool_gateway/03_tool_schema.md`'s
schema registry — a tool invocable but absent from this table is a specification gap to close.
