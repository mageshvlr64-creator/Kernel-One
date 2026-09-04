# Timeout Policy

> Restates the timeout column of `11_retry_policy.md`'s canonical table with explicit
> cleanup-on-timeout behavior per operation class — this file is the "what happens at the
> moment of timeout" detail; `11_retry_policy.md` is the canonical numbers.

## Cleanup behavior by operation class

| Operation class | On timeout, what's cleaned up |
|---|---|
| `model-inference` | In-flight generation is cancelled at the provider (not just abandoned client-side — the provider is explicitly told to stop, freeing its GPU slot for the next request) |
| `tool-heavyweight` (code execution) | The container is killed (`docker kill`, not a graceful stop) and removed per `features/09_code_execution/11_container_cleanup.md` — no orphaned container survives a timeout |
| `document-processing` | The specific page/stage in progress is marked failed; already-completed pages/stages are NOT re-processed on retry (idempotent per-page tracking) |
| `interactive-write` | The database transaction is rolled back — no partial write survives a timeout, consistent with `failures/40_audit_failures.md`'s all-or-nothing rule |

## Rule

A timeout must never leave a resource (container, transaction, file handle, GPU allocation)
held indefinitely — every operation class's timeout handler explicitly releases what it held,
verified by `testing/23_failure_injection.md`'s failure-injection tests.
