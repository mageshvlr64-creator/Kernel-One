# Backpressure

> How the system signals "slow down" to callers before a queue (`17_queueing.md`) fills
> completely, rather than only failing once full.

## Mechanism

As a queue (e.g. model-inference request queue) approaches its depth limit, the API layer's
rate limiter (`schemas/02_api_schema.md`, `RATE_LIMIT_PER_MINUTE`) is the primary backpressure
signal a client experiences — `429 RATE_LIMITED` responses increase in frequency as load
increases, giving well-behaved clients (retrying with backoff per the `Retry-After` header) a
signal to slow down before the queue actually overflows into
`MODEL_RESOURCE_EXHAUSTED`/`SANDBOX_LIMIT_EXCEEDED` territory.

## Relationship to rate limiting vs. queueing

Rate limiting (`schemas/02_api_schema.md`) is a per-user request-frequency control; queueing
(`17_queueing.md`) is a per-resource concurrent-load control — both exist because a single
user hitting the rate limit and many users collectively filling a resource queue are different
problems requiring different signals, and V1 implements both rather than relying on one alone.
