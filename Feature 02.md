# Feature 02 — Agent Kernel

## Purpose
The core differentiator (your source doc's Section 3). It turns "user asked X" into an explicit, ordered, inspectable execution graph instead of a black-box model call. This is what your UI renders as the live checklist and what the audit log persists.

## How to build

1. **Task object** — on every user message, create a `Task` row: `{task_id, user_id, input_text, status, created_at}`.
2. **Plan step** — the kernel calls the Model Router (Feature 01) to classify the task, then builds a static list of steps appropriate to that task type. For 14 days, use a **small set of hardcoded step templates** keyed by task tag (`document_qa`, `coding`, `general`) rather than a fully dynamic planner — a dynamic LLM-generated plan is a nice-to-have, not required for a convincing demo, and it's a reliability risk under time pressure.
   - `document_qa` template: `classify → select_model → retrieve_context → generate_answer → attach_citations → (optional) human_approval → (optional) generate_artifact`
   - `coding` template: `classify → select_model → call_tool:sandbox → verify_output → (optional) human_approval`
3. **Step executor** — each step is a small async function with a consistent signature `(task, context) -> step_result`. The kernel runs them in order, updating `status: pending → running → done/error` after each, and **pushes each transition over the WebSocket immediately** — this is what makes the UI feel alive rather than showing a spinner then a wall of text.
4. **Persistence** — every step transition is also written to the audit table (Feature 10) as it happens, not batched at the end — if the process crashes mid-task, you still have a partial, honest record.
5. **Human approval gate** — certain step templates include a `human_approval` step that the executor does not auto-advance past; it waits for an explicit API call from the UI (Feature 09) before continuing.

## Data/API contract

```json
{
  "task_id": "uuid",
  "steps": [
    {"name": "classify", "status": "done", "detail": "document_qa"},
    {"name": "select_model", "status": "done", "detail": "qwen2.5-1.5b"},
    {"name": "retrieve_context", "status": "running"},
    {"name": "generate_answer", "status": "pending"}
  ]
}
```
WebSocket pushes this object (or a diff of it) on every step transition.

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| UI shows a step stuck on "running" forever | A step function threw an unhandled exception | Wrap every step executor in try/except; on exception, set `status: error`, push it to UI immediately, log to audit — never let a task hang silently |
| Execution graph and audit log disagree about what happened | Step transition written to one but not the other due to ordering bug | Write to audit log and push to WebSocket from the same function call, not two separate code paths |
| Kernel re-runs a step after approval instead of resuming | Approval handler restarts the task instead of resuming from the paused step index | Store the paused step index on the task row; the resume handler must continue the loop from that index, not from step 0 |
| Long-running step (e.g. a slow model call) blocks the whole server | Synchronous call inside an async step function | Use `asyncio.to_thread` (or run inference in a subprocess/thread pool) for any blocking model/tool call |
| Two tasks from the same user interleave incorrectly in the UI | Task ID not included in every WebSocket message, or single global state variable used instead of per-task state | Every message and every internal state dict must be keyed by `task_id` |

## Definition of Done
A `document_qa` task and a `coding` task both run end-to-end through their full step templates, both visibly pause at their approval gate, both resume correctly on approval, and the final audit log for each task exactly matches what the UI displayed live.
