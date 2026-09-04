# Data Classification Levels (Reference)

> Canonical definition, referenced by `features/20_data_classification/` and every entity
> carrying a `classification` field (`domain/`).

| Level | Definition | Who can access (role clearance) | Model restriction | Export restriction |
|---|---|---|---|---|
| `PUBLIC` | No sensitivity; safe for any audience | All roles | Any approved model | No restriction |
| `INTERNAL` | Default level; organization-internal, not sensitive | All roles (default clearance) | Any model with `max_classification >= INTERNAL` | No restriction |
| `CONFIDENTIAL` | Sensitive; limited distribution within the organization | Clearance `CONFIDENTIAL` or `RESTRICTED` only | Only models explicitly approved to `CONFIDENTIAL` (`schemas/06_model_schema.md` `max_classification`) | Requires Approval (REQ-FUNC-003) |
| `RESTRICTED` | Highest sensitivity; named-individual access only | Clearance `RESTRICTED` only | Only models explicitly approved to `RESTRICTED` | Requires Approval; export logged with heightened audit detail |

## Ordering

`PUBLIC` < `INTERNAL` < `CONFIDENTIAL` < `RESTRICTED` — a user's clearance must be greater than
or equal to a resource's classification to read it; this comparison is the entirety of the
classification check (combined with the workspace/role conditions in
`reference/05_permission_matrix.md`).

## Propagation

See `domain/01_domain_model.md` cross-cutting rule 1 and REQ-DATA-001 — classification only
ever propagates upward (a derived entity's classification is never lower than any of its
sources').
