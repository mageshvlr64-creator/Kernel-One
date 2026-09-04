# Unit Testing

> One test per function/failure-mode, no external dependencies (database, network, other
> services) — mocked or stubbed per the adapter pattern in `integrations/01_integration_architecture.md`.

## Rule

Every failure mode listed in a `docs/failures/` file has at least one unit test asserting: the
trigger condition produces exactly the documented error code, and no partial state is left
behind. A failure mode with no corresponding unit test is a gap flagged in
`08_BUILD_PHASES.md`'s phase exit review.

## Scope boundary

Unit tests never touch a real database, real object storage, or a real model runtime — those
are integration tests (`03_integration_testing.md`). A "unit test" that spins up Docker or
hits PostgreSQL is miscategorized and should be moved.
