# Testing Strategy (Index)

> Canonical test pyramid and the shared conventions every test file below follows.

## Pyramid

```
        /  E2E (demo scenarios, TEST-E2E-*)  \
       /  Integration (per-feature, cross-service)  \
      /  Contract (API schema conformance)  \
     /  Unit (per-function, per-failure-mode)  \
```

## Coverage requirement (per `13_DEVELOPER_RULES.md`)

Every feature file's "Test requirements" section names: one unit test per row in its Failure
modes table, one integration test for the success path, and one permission test per role in
`reference/05_permission_matrix.md`. This directory defines *how* each category of test is
written; the feature files define *what* must be tested.

## Test ID registry

All named test IDs (`SEC-TEST-*`, `TEST-*`) are tracked in `reference/13_test_matrix.md` —
this directory's files describe methodology; specific test case tables live in
`21_security_testing.md` (security) and are referenced, not duplicated, elsewhere.
