# Failure Handling Philosophy

> Canonical principles every file in this directory follows. Individual failure files
> (`03_user_errors.md` onward) apply these principles to a specific trigger; they do not
> restate the principles themselves.

## Principles

1. **Fail loud, never silent.** Every failure surfaces a specific error code
   (`reference/01_error_codes.md`) to the caller and an `AuditEvent` to the trail
   (REQ-AUD-001) — a caught-and-ignored exception is always a defect.
2. **Fail closed on authorization ambiguity.** If it's unclear whether an action is permitted
   (e.g. the Policy Engine is unreachable), the default is deny (REQ-SEC-001).
3. **No unaudited state change, ever** — including on the failure path
   (`failures/40_audit_failures.md`'s "transaction rolls back if audit can't be written" rule
   is the strictest expression of this).
4. **Distinguish user error from system failure.** A `400`-class error (caller's mistake) is
   never retried automatically and never treated as an incident; a `5xx`-class error may be
   retried per `runtime/11_retry_policy.md` and may be an incident if sustained.
5. **Partial completion is explicit, never implicit.** A multi-step operation's completed steps
   stand; failed/blocked steps are clearly marked — nothing is left in an ambiguous
   in-between state (`44_partial_failure_recovery.md`).
6. **Refuse over fabricate.** Where correctness can't be established (e.g. no evidence for a
   claim, REQ-FUNC-005), the system declines to state the claim rather than guessing.

## How to use this directory

Each file below names one failure class: its trigger, detection mechanism, system response,
canonical error code, and recovery path. A feature document's own "Failure modes" section
references the relevant file(s) here rather than re-describing the failure.
