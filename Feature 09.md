# Feature 09 — Human Approval System

## Purpose
No AI-generated artifact or high-impact tool call goes out the door without an explicit human click — this is the "human-in-the-loop" enforcement your source doc calls for, and it's a cheap, high-visibility feature: it's mostly UI + one pause point in the kernel, not new ML.

## How to build

1. **Define approval-gated step types** — decide upfront which step templates (Feature 02) include a `human_approval` step, e.g. before artifact generation, or before any tool call marked `security_class: sensitive`. Keep this list short and explicit, not "everything needs approval" (that would make the demo tedious) or "nothing needs approval" (defeats the point).
2. **Pause, don't fake-pause** — when the kernel reaches a `human_approval` step, it must genuinely stop executing further steps and persist `status: awaiting_approval` on the task — don't just show a UI overlay while the backend keeps going (a subtle but common bug under time pressure).
3. **Approval UI** — render the pending item clearly: what will happen if approved (e.g. "Generate and download inspection_approval_note.docx with these 3 findings"), with Approve/Reject buttons. Show the actual content to be approved, not just a generic "approve?" — this is what makes it a meaningful gate rather than theater.
4. **Resume on approval** — the Approve action calls an endpoint that updates the task's status and calls back into the kernel to resume from the paused step index (see Feature 02's failure table — resume from index, not restart).
5. **Reject path** — Reject should cleanly end the task with a `rejected` status, logged, no artifact generated, no further tool calls made — and the UI should acknowledge this explicitly rather than just going quiet.
6. **Log both outcomes** — approval and rejection are both first-class audit events with a timestamp and (if you add auth) which user approved/rejected.

## Data/API contract

```json
POST /tasks/{task_id}/approve  -> {"status": "approved", "resumed_at_step": 4}
POST /tasks/{task_id}/reject   -> {"status": "rejected"}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Backend keeps working during "pending approval" | Approval gate implemented as a UI-only delay (e.g. `setTimeout`) instead of a real kernel pause | The kernel's step loop must literally `return`/`await` on an external signal at that step — verify by checking no audit events are written between the pause and the approve click during a manual test |
| Approving twice (double-click) runs the downstream steps twice | No idempotency check on the approve endpoint | Check task status before resuming; if already `approved`/past that step, no-op the second call |
| Reject doesn't actually stop everything (artifact still generated) | Reject handler updates status but the kernel loop wasn't actually blocked, so it proceeds anyway | Same root cause as the first failure — fix at the pause mechanism, not the reject handler |
| Judges don't notice the approval step because it looks like decoration | Approval UI too subtle / auto-scrolls past it | Make the pending-approval state visually distinct (color, explicit modal or banner) — this is a demo moment, not a background detail |
| Task stuck forever if nobody clicks approve during the demo | No timeout/expiry handling | Not a blocker for the demo (you control when you click approve), but note it as a known limitation rather than a claimed production feature if asked |

## Definition of Done
A task visibly halts at a human-approval step with the actual pending content shown; clicking Approve resumes and completes the task; clicking Reject on a separate run cleanly ends the task with nothing generated; both outcomes appear correctly in the audit log.
