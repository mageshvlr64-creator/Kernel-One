# Feature 10 — Audit Log

## Purpose
An append-only record of everything the system did — every kernel step, every routing decision, every tool call (allowed or denied), every approval/rejection. This is what turns "auditable" from a marketing word into a feature judges can click into and inspect.

## How to build

1. **Schema (SQLite table, e.g. `audit_events`)**: `id (autoincrement PK), task_id, timestamp, event_type, detail_json, user_id`. Keep it flat and simple — one row per event, not a nested structure, so it's trivially queryable and displayable as a table.
2. **Write-through, not batch** — every other feature (Kernel, Router, Tool Gateway, Approval) writes to this table **at the moment the event happens**, not at the end of the task. This was already called out in Feature 02's failure table because it's the single most common shortcut that quietly breaks the audit story under time pressure.
3. **Append-only enforcement** — don't build any UPDATE/DELETE path for this table in the app. For the hackathon, "append-only" can be enforced at the application layer (no code path ever updates/deletes rows); a full DB-level immutability guarantee (e.g. a write-once log, hash chaining) is a nice stretch mention in the pitch but not required to build.
4. **Audit UI** — a simple table/timeline view filterable by `task_id`, showing event type, timestamp, and expandable detail JSON. This is the screen you show right after the approval step in the demo script.
5. **Optional integrity touch (if time allows, Day 13 slack)** — store a rolling hash of each event chained to the previous event's hash (`hash_n = sha256(event_n + hash_{n-1})`). This lets you demonstrate "if anyone tampered with this log, the chain breaks" — a strong, cheap-to-implement claim for the "reproducible/auditable" pitch. Not required for Definition of Done below, but a good bonus line if Day 13/14 has room.

## Data/API contract

```json
{"id": 1042, "task_id": "uuid", "timestamp": "...", "event_type": "tool_call_denied",
 "detail_json": {"tool": "sandbox_exec", "role": "viewer", "reason": "lacks code_execution permission"}}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Some events missing from the log (e.g. denials, or router decisions) | Logging added to the "happy path" only, not error/denial branches | Audit against Features 01, 02, 05, 09's own failure tables — each explicitly calls out "log this too"; treat missing-log as a bug in that feature, not acceptable |
| Log grows too large / slow to query during the demo | No indexing, or querying the whole table instead of filtering by `task_id` | Add an index on `task_id`; always filter the UI query by the current task, never `SELECT *` the whole table live |
| Audit UI shows raw JSON dumps that are unreadable to a judge | No formatting layer between raw event and display | Write a small per-`event_type` renderer (a few if/else cases) that turns `detail_json` into a one-line human-readable sentence, falling back to raw JSON only for unknown types |
| Two processes/threads write to SQLite concurrently and corrupt/lock the DB | Multiple async tasks writing without care | Use a single DB connection with proper async-safe access (e.g. a lightweight write queue, or SQLModel/SQLAlchemy's session handling) — don't open ad-hoc raw `sqlite3.connect()` calls from multiple places |
| "Audit" claim undermined because the log can trivially be edited from a Python shell during the demo | No real enforcement, just a mention in the pitch | Be precise in the pitch about what's actually enforced (app-layer append-only + optional hash chain) vs. what would need production hardening — honesty here reads better to technical judges than an overclaim that falls apart under a follow-up question |

## Definition of Done
Every event type produced elsewhere in the system (routing decision, kernel step transition, tool allow/deny, approval/rejection, artifact generation) appears in the audit table with a correct `task_id` and timestamp, viewable and readable in the Audit UI for a completed demo task.
