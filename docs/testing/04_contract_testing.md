# Contract Testing

> Verifies that every API endpoint's actual request/response shape matches
> `docs/api/` and `docs/schemas/` exactly — catching drift between specification and
> implementation before it reaches integration/E2E tests.

## Method

Generate test requests from the JSON Schema examples in `docs/schemas/*.md`; assert the live
endpoint accepts valid examples and rejects invalid ones with `INVALID_REQUEST` and the
correct field-level `details`. Response shape is validated against the same schema.

## Rule

A contract test failure means either the code or the doc is wrong — per
`13_DEVELOPER_RULES.md` rule 2, the fix always updates both to match, never just silences the
test.
