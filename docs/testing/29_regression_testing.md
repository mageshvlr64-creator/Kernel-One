# Regression Testing

> The full test suite (all categories above) re-run on every change, gating merge per
> `08_BUILD_PHASES.md` Phase 0's CI pipeline.

## Composition

Unit + Integration + Contract + API tests run on every commit (fast feedback); Security +
E2E + Performance + Load tests run on a nightly/pre-release schedule (slower, more expensive)
plus always before a release per `reference/14_release_matrix.md`'s gates.

## Rule

A regression is any previously-passing test that now fails — per `13_DEVELOPER_RULES.md`
rule 2, a regression is fixed before new work continues on the same area, not deferred.
