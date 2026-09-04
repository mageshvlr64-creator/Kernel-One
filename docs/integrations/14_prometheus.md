# Prometheus Integration

> Metrics scraping backend for `features/25_observability/03_metrics.md`, exposed via each
> service's `/metrics` endpoint (`api/25_metrics_api.md`).

## Contract

Standard Prometheus text-exposition format; Prometheus itself runs on-premise within the
deployment boundary and scrapes internal service endpoints only — no remote-write to an
external SaaS metrics backend by default (would require an explicit `restricted`-mode
allowlist entry and its own `DECISION REQUIRED` review if ever needed).

## Key metrics exposed

Per-operation-class latency histograms (`performance/`), per-feature invocation counters
(matching each feature file's "Observability requirements" section,
`event_type`-aligned naming).
