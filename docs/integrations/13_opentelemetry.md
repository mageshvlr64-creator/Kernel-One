# OpenTelemetry Integration

> Tracing/metrics instrumentation library used across all services for
> `features/25_observability/`.

## Contract

Each service instruments its own request handlers with OTel spans; the collector endpoint
(`OTEL_EXPORTER_ENDPOINT`, `16_ENVIRONMENT_AND_CONFIGURATION.md`) must resolve to a
`localhost`/internal address — never an external SaaS observability backend, per REQ-NET-001.

## Failure isolation

See `failures/39_observability_failures.md` — a collector outage never blocks or slows the
request being instrumented; telemetry loss is tracked separately from application failures.
