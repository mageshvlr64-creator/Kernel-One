# Integration Testing

> Tests exercising a real database (test instance), real object storage (test bucket), and
> real service-to-service calls within one host — the level at which
> `10_DEPENDENCY_GRAPH.md`'s edges are actually verified as working, not just assumed.

## What belongs here

- A feature's full success path end-to-end within its own service boundary (e.g. Document
  Ingestion's full UPLOADED→READY state progression against a real test document).
- Cross-service calls that don't require a full UI/demo scenario (e.g. Tool Gateway correctly
  calling into the Policy Engine and getting a real allow/deny decision).

## What does NOT belong here

Full end-to-end user scenarios spanning UI+API+multiple services — those are `07_agent_testing.md`
and the `TEST-E2E-*` cases referenced from `demo/`.
