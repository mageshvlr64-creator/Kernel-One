# Retry, Timeout, Backoff and Circuit-Breaking Policy (Canonical)

> **Canonical owner** of every timeout, retry, and backoff value in the system. No feature
> document may define its own timeout/retry number; it references an operation class below.
> Every number here is labeled with its provenance per the Upgrade Prompt's precision rule:
> **CONFIG DEFAULT** (an implementation default, changeable, not benchmark-derived),
> **DESIGN LIMIT** (a deliberate ceiling with stated rationale), or **BENCHMARKED**
> (backed by a specific measurement — cite the source).

## Operation classes

| Class | Example operations | Timeout | Max retries | Retryable on | Backoff | Max backoff | Circuit breaker | Provenance |
|---|---|---|---|---|---|---|---|---|
| `interactive-read` | Model registry read, permission check, list documents | 2s | 1 | `DEPENDENCY_UNAVAILABLE` | fixed 100ms | 100ms | Open after 10 consecutive failures in 30s; half-open probe every 15s | CONFIG DEFAULT — chosen to keep UI responsive; not load-tested |
| `interactive-write` | Create task, upload metadata write, approval decision | 5s | 0 (writes are not auto-retried; see rationale below) | — | — | — | Open after 10 consecutive failures in 30s | DESIGN LIMIT — writes are not automatically retried by default because most write endpoints are not yet guaranteed idempotent (see `runtime/15_idempotency.md`); a client MAY manually retry using the `idempotency_key` field |
| `model-inference` | Text/vision generation call to inference gateway | 30s (text), 60s (vision, larger context) | 1 | `MODEL_UNAVAILABLE`, `INFERENCE_TIMEOUT` | fixed 500ms | 500ms | Open after 5 consecutive failures for the same model in 60s → router falls back per `features/02_model_router/09_fallback_routing.md` | CONFIG DEFAULT — 30s/60s chosen as a usability ceiling for the reference hardware profile (PROFILE-B); not yet benchmark-verified against final model selection (`20_DECISION_LOG.md` DEC-014) |
| `tool-lightweight` | Calculator, filesystem read < 1MB | 5s | 1 | `DEPENDENCY_UNAVAILABLE` | fixed 200ms | 200ms | Open after 10 consecutive failures in 30s | CONFIG DEFAULT |
| `tool-heavyweight` | Code execution, database query, spreadsheet analysis | 60s | 0 (not auto-retried — side effects may not be idempotent) | — | — | — | Open after 5 consecutive failures for the same tool in 60s | DESIGN LIMIT — 60s matches the sandbox's own hard execution timeout (`features/09_code_execution/09_execution_timeout.md`) so the tool gateway timeout never fires before the sandbox's own cleanup |
| `document-processing` | OCR page, PDF parse, chunking/embedding a document | 120s per document | 1 | `DEPENDENCY_UNAVAILABLE`, `RAG_INDEX_UNAVAILABLE` | fixed 2s | 2s | Open after 5 consecutive failures in 5 minutes | CONFIG DEFAULT — 120s chosen to cover a 50-page scanned document on CPU-only OCR (PROFILE-A); not yet benchmarked |
| `artifact-generation` | DOCX/PPTX/XLSX/PDF rendering | 30s | 1 | `DEPENDENCY_UNAVAILABLE` | fixed 1s | 1s | Open after 5 consecutive failures in 60s | CONFIG DEFAULT |
| `background-job` | Backup, index rebuild, batch reprocessing | 4 hours | 1 | any transient dependency error | fixed 60s | 60s | N/A (single long-running job, not a rapid retry loop) | CONFIG DEFAULT |

## Rules

1. Retry is only ever applied to the error codes explicitly listed under "Retryable on"
   (`reference/01_error_codes.md`); it is never applied to `4xx` validation/authorization
   errors.
2. A retried call MUST carry the same `idempotency_key` on every attempt where the operation
   class supports one; if it doesn't, the operation is not auto-retried (see
   `interactive-write`, `tool-heavyweight`).
3. Circuit breaker state is tracked per-dependency (e.g. per model ID, per tool ID), not
   globally — one failing model must not open the breaker for a healthy one.
4. When a circuit breaker is open, calls fail immediately with `DEPENDENCY_UNAVAILABLE` (or
   `MODEL_UNAVAILABLE` for model calls) rather than waiting out the timeout.
5. Any number in this table not yet marked BENCHMARKED must be re-validated against real
   hardware/model measurements before the V1 hardening phase (`08_BUILD_PHASES.md` Phase 10)
   and either confirmed (relabel BENCHMARKED with source) or revised.

## How feature documents use this file

A feature document's "Retry behavior" / "Timeout behavior" sections state only which operation
class the feature's calls belong to: "This is a `tool-heavyweight` operation; see
`runtime/11_retry_policy.md` for the exact values." They do not state their own numbers.
