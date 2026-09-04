# Runtime Invariants

> The "always true" statements every file in this directory assumes — the runtime-layer
> analog of `security/25_security_invariants.md`.

1. **A state transition is only committed after its side effect completes**
   (`14_resume_and_recovery.md`) — never the reverse, which would let a crash claim work
   happened that didn't.
2. **No resource (container, transaction, GPU slot, lock) is held past its operation's
   timeout** (`12_timeout_policy.md`) — verified by `testing/23_failure_injection.md`.
3. **A non-idempotent operation is never automatically retried** (`15_idempotency.md`) —
   automatic retry is opt-in per operation, not a default behavior applied uniformly.
4. **Concurrent Tasks share no mutable state outside the database's own locking**
   (`16_concurrency.md`) — no in-memory cross-task shared state exists that could leak or
   corrupt across Task boundaries.
5. **A queue-full condition returns a specific resource-exhaustion error, never blocks
   indefinitely** (`17_queueing.md`) — every queue has a bounded depth and a defined
   overflow behavior.
6. **No Task remains in a non-terminal state indefinitely without either progressing or being
   explicitly failed by the reconciliation job** (`14_resume_and_recovery.md`'s grace-period
   bound).

## Verification

Each invariant above should have a corresponding `testing/23_failure_injection.md` or
`testing/27_recovery_testing.md` case — an invariant with no test verifying it under real
failure conditions is asserted but not confirmed, and should be prioritized when expanding
test coverage.
