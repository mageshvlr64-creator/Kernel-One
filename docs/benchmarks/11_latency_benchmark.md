# Latency Benchmark

> The empirical measurement feeding `performance/02_latency_budgets.md`'s targets and
> resolving DEC-014's pending validation, once a model is pinned (DEC-013).

## Method

Measure first-token and full-response latency for each capability slot's candidate model on
the actual target hardware profile (PROFILE-B), across a realistic distribution of prompt
lengths/context sizes — not just a single best-case measurement.

## Output

A BENCHMARKED-labeled replacement for every currently DESIGN-LIMIT-labeled latency number in
`performance/02_latency_budgets.md` and `runtime/11_retry_policy.md`'s `model-inference`
timeout row, once this benchmark has actually run against the pinned model.
