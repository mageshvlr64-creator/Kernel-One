# Service Restart / Partial Failure Recovery

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

runtime/14_resume_and_recovery.md

## Steps

1. A backend service restarts mid-task (e.g. agent-kernel process crash)
2. In-flight Task remains in its last durably-persisted state (state machine transitions are only committed after their side effect, not before)
3. On restart, a reconciliation job identifies tasks stuck in EXECUTING beyond a grace period and either resumes (if the AgentRun's plan is still valid) or fails them explicitly with a recovery-specific error, never leaving them silently stuck

## Notes

—
