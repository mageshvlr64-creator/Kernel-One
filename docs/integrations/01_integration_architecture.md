# Integration Architecture

> How every third-party component is wrapped, so a swap of any one never leaks into
> application code beyond its adapter — the concrete pattern behind DEC-004's
> multi-provider inference design and every other integration below.

## Pattern

Every integration in this directory is accessed through exactly one adapter module
(`packages/` or the owning service's own `adapters/` subfolder per
`15_CODEBASE_TARGET_STRUCTURE.md`) implementing a fixed interface the rest of the application
depends on — never the third-party library's native API surface directly from business logic.

## Why this matters for sovereignty specifically

An adapter is also the enforcement point for "this library doesn't phone home" — since a
raw third-party library call bypassing the adapter is exactly the gap
`security/14_network_bypass.md` and the egress-guard pattern
(`features/18_network_sovereignty/`) are designed to catch, keeping all such calls behind a
reviewed adapter reduces the surface that needs auditing.

## Failure policy

See `16_integration_failure_policy.md` for the shared failure-handling rule every integration
below follows.
