# Test Matrix (Reference)

> Consolidated list of every named test ID referenced across this specification, with its
> owning file — cross-checked against `17_SOURCE_TRACEABILITY.md`'s requirement mapping.

| Test ID | Defined in | Covers |
|---|---|---|
| `TEST-NET-001`, `002`, `003` | `testing/18_network_testing.md` (via `security/02_threat_model.md` references) | REQ-NET-001/002/003 |
| `SEC-TEST-001` through `008` | `testing/21_security_testing.md` | REQ-SEC-*, REQ-FUNC-004 |
| `TEST-E2E-001`, `002` | `demo/` scenario acceptance | REQ-FUNC-001, REQ-FUNC-002 |
| `TEST-APPROVAL-001` | `features/16_human_approval/` test requirements | REQ-FUNC-003 |
| `TEST-ROUTER-004`, `005` | `features/02_model_router/` test requirements | REQ-AI-001, REQ-AI-003 |
| `TEST-OCR-001` | `features/11_ocr/` test requirements | REQ-AI-002 |
| `TEST-EVIDENCE-001` | `features/14_evidence_and_provenance/` test requirements | REQ-FUNC-005 |
| `TEST-CLASS-001` | `features/20_data_classification/` test requirements | REQ-DATA-001 |
| `TEST-AUDIT-001`, `002` | `features/17_audit/` test requirements | REQ-AUD-001, REQ-SEC-005 |
| `TEST-PERF-001` | `performance/` budget files | REQ-PERF-001 |

## Rule

Every test ID appearing anywhere in this specification must appear in this table — an
untracked test ID mentioned in a feature file but absent here is a documentation gap to close.
