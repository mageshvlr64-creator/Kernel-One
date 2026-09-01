# Feature 12 — Role-Based Access Control (RBAC)

## Purpose
The enforcement layer that makes "permission-aware" real rather than a slide bullet. Your source doc (Section 22) lays out a fuller role ladder (Employee, Engineer, Reviewer, Manager, Admin, Security Admin, AI Admin, Auditor) and data-classification scheme (Section 23: PUBLIC → TOP SECRET). For a 14-day solo build, scope this down to **2 roles that actually get exercised in the demo** — everything beyond that is a slide mention, not a build target (see `03_HARDWARE_CONSTRAINTS.md`'s "everything not in the 12-feature V1 list is out" rule).

## How to build

1. **V1 role scope** — implement exactly two roles: `admin` (full access — chat, upload, code execution, approvals, audit view) and `restricted` (chat + upload only, no code execution, no approvals). This is the minimum needed to make Feature 05's Tool Gateway demo ("blocked for restricted, allowed for admin") real. Keep the fuller 8-role ladder from your source doc as a documented "V2 roadmap" note in this file or the README — mentioning it in the pitch as a designed-for-extension is fine; building all 8 roles is not a good use of 14 days.
2. **User/role table** — a simple SQLite table (`users`: `id, username, role`) seeded with 2-3 hardcoded demo users at startup (no self-registration/signup flow needed — this is a hackathon demo, not a product with an onboarding funnel). A simple session cookie or even a UI dropdown "logged in as: [admin ▾]" that sets the active user is enough; don't build real auth (password hashing, JWT, OAuth) unless you have slack time — it adds risk for zero demo value.
3. **Permission table** — a plain mapping, `role → set of allowed capabilities`, where capabilities match the `security_class` values already used by the Tool Gateway (Feature 05): e.g. `{"admin": ["chat", "upload", "code_execution", "approve", "view_audit"], "restricted": ["chat", "upload"]}`. Keep this as a small in-memory dict or a one-table lookup — no need for a generic policy DSL.
4. **Enforcement point — one place only** — every capability check happens inside the Tool Gateway (Feature 05) and the Human Approval handler (Feature 09), not scattered across route handlers. A request for a disallowed capability is rejected there, logged to the audit table (Feature 10) with the role and the missing capability, and returned to the UI as a clear "blocked: requires `code_execution` permission" message — never a silent no-op or a generic 500 error.
5. **Data-classification note (documented, not built)** — your source doc's classification scheme (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED/TOP SECRET) determining which models/tools may touch a document is a strong V2 pitch point ("every document could carry a classification that further restricts which local model and tools may process it") but is explicitly out of V1 scope per the README's ground truth — don't build a classification field into the document schema unless Day 13/14 has slack; if you do, the minimum viable version is a single `classification` column on the document row that the Tool Gateway checks alongside role, nothing more.
6. **UI surface** — a small role switcher (dropdown or two demo login buttons: "Log in as Admin" / "Log in as Restricted User") so the demo can show the same action succeeding for one and failing for the other back-to-back, without restarting the app.

## Data/API contract

```json
// Tool Gateway permission check (extends Feature 05's contract)
{
  "user_id": "u2",
  "role": "restricted",
  "requested_capability": "code_execution",
  "allowed": false,
  "reason": "role 'restricted' lacks capability 'code_execution'"
}
```

```json
// users table row
{"id": "u1", "username": "demo_admin", "role": "admin"}
{"id": "u2", "username": "demo_restricted", "role": "restricted"}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| A restricted user can still trigger a blocked action through a different route (e.g. artifact generation instead of the sandbox) | Capability checks added to some endpoints but not others — enforcement scattered instead of centralized | Route every capability-gated action through the single Tool Gateway/Approval check points (step 4) — never add a second, ad-hoc permission check inline in a route handler |
| Role switch in the UI doesn't actually change backend behavior | UI dropdown only changes a display label, not the session's actual user/role used by the backend | The role switcher must set the real active session identity used by every subsequent API/WebSocket call, not a cosmetic frontend flag |
| Demo's "blocked" case looks identical to a generic error, undermining the RBAC story | Rejected request returns a raw exception/500 instead of a structured denial | Return a structured `{"allowed": false, "reason": "..."}` response and render it distinctly in the UI (e.g. a red "🔒 blocked by role" message), not a stack trace |
| RBAC denial not visible in the audit log | Denial handled and returned to the UI before the audit write happens, or audit write skipped on the error path | Same rule as Feature 10's failure table: log at the moment of denial, in the same code path as the rejection, not just on the success path |
| Scope creep into the full 8-role/5-classification system eats build days | Source doc's fuller enterprise model treated as the target instead of the V1-scoped 2-role version | Re-read this file's step 1 and 5 before touching RBAC code — V1 is 2 roles, no classification field, full stop until Day 14 is stable |

## Definition of Done
Logging in as `restricted` and attempting a code-execution request is visibly blocked in the UI with a clear reason, the same request succeeds when logged in as `admin`, both outcomes are logged to the audit table with role and capability detail, and switching between the two demo users requires no app restart.
