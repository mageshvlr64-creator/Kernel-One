# Error States

> Canonical error-state rendering rules. Screen files reference this rather than each
> inventing their own error UI.

## Rule

Every error state renders the `ErrorBanner` component (`02_design_system.md`) with exactly the
`code` and `message` from `reference/01_error_codes.md` — never a raw exception, stack trace,
or generic "Something went wrong" when a specific code is available.

## Layout by severity

| Severity | Presentation |
|---|---|
| Field-level (`INVALID_REQUEST` with `details`) | Inline under the specific form field |
| Action-level (`POLICY_DENIED`, `RESOURCE_CONFLICT`) | Toast/banner near the triggering control, auto-dismiss after 8s but re-openable from a history icon |
| Page-level (`DEPENDENCY_UNAVAILABLE` blocking the whole screen) | Full-content-area banner replacing the screen, with a Retry button |
| System-level (`INTERNAL_ERROR`) | Full-content-area banner + the `correlation_id` shown for the user to reference when contacting support |

## Retry affordance

Any error with `Retryable: Yes` in the error registry shows a "Retry" button that re-issues
the exact same request (same `Idempotency-Key` if one was used); errors marked not retryable
do not show a Retry button at all, to avoid implying an identical retry would help.
