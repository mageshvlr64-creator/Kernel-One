# Role Matrix (Reference)

> Restates `05_permission_matrix.md`'s role list as a standalone quick-reference, plus which
> roles are V1-demo-rehearsed (DEC-006) vs. schema-only.

| Role | V1 demo-rehearsed? | Primary purpose |
|---|---|---|
| `Administrator` | Yes (DEC-006) | Full system access, approvals, user/policy management |
| `SecurityOfficer` | No (schema/policy-engine complete, not demo-polished) | Approvals, full audit visibility, no user management |
| `Operator` | No | Model/deployment/system-health management |
| `Analyst` | No | Standard end user with elevated tool access vs. Restricted User |
| `RestrictedUser` | Yes (DEC-006) | Chat + upload only, demonstrates the RBAC-denial beat |
| `Auditor` | No | Read-only audit/config history access |

## Full permission detail

See `05_permission_matrix.md` for the resource/action grid — this file is the role list only.
