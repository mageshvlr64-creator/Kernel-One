# Idempotency

> Which operations are safely retryable, and the mechanism (`Idempotency-Key`,
> `schemas/02_api_schema.md`) that makes retries safe where they are.

## Idempotent operations (safe to retry with the same key)

- Task creation (`POST /api/v1/tasks`) — a retried request with the same `Idempotency-Key`
  returns the original Task rather than creating a duplicate.
- Document upload — deduplicated by `sha256` (`domain/06_document_model.md`) regardless of
  `Idempotency-Key`, as a second layer of protection.
- Approval decisions — a retried identical decision is a no-op returning the original result;
  a *different* decision on an already-decided Approval is `RESOURCE_CONFLICT`
  (`failures/41_approval_failures.md`), not silently accepted.

## Non-idempotent operations (never auto-retried, per `11_retry_policy.md`)

- Code execution (`tool-heavyweight`) — side effects (files written, external-adjacent state
  even within the sandbox) may not be safely repeatable.
- Any write whose effect depends on current state in a way a retry could double-apply (e.g.
  "append this line" operations, if any exist) — these require an explicit idempotency
  mechanism (a sequence number, or the `Idempotency-Key` pattern above) before being marked
  safe to retry, not retried by default.

## Rule

An operation is idempotent-safe-to-retry only if this file explicitly says so — the default
assumption for any new operation is "not idempotent" until proven and documented otherwise.
