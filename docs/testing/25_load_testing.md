# Load Testing

> Sustained/high-volume testing, distinct from `24_performance_testing.md`'s single-operation
> latency focus — verifies `performance/07_concurrency_limits.md`'s queuing behavior under
> real concurrent load.

## Required tests

- Ramp concurrent Task creation up to and beyond PROFILE-B's expected concurrency
  (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) — verify graceful queuing, not cascading
  failure, once limits are reached.
- Sustained load at the `RATE_LIMIT_PER_MINUTE` boundary — verify `429 RATE_LIMITED` behavior
  is correct and doesn't itself become a bottleneck (e.g. rate-limit-check overhead should be
  negligible per `performance/07_concurrency_limits.md`).
