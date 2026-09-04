# Codebase Target Structure

> Canonical target source tree. Code must converge on this layout; `docs/13_DEVELOPER_RULES.md`
> governs how it is written, this file governs where it lives.

```
sovereign-workbench/
├── apps/
│   └── workbench-ui/            # Frontend (React) — ui/, workflows/ implemented here
├── services/
│   ├── api/                     # HTTP/WS API layer — api/ contracts implemented here
│   ├── agent-kernel/            # features/04_agent_kernel/
│   ├── model-router/            # features/02_model_router/
│   ├── inference-gateway/       # features/03_inference_gateway/ (+ provider adapters)
│   ├── tool-gateway/            # features/05_tool_gateway/ + individual tool implementations
│   │   └── tools/
│   │       ├── filesystem/      # features/06_filesystem_tool/
│   │       ├── calculator/      # features/07_calculator_tool/
│   │       ├── database/        # features/08_database_tool/
│   │       └── code_execution/  # features/09_code_execution/
│   ├── document-pipeline/       # features/10_document_ingestion/, 11_ocr/, 12_multimodal/
│   ├── knowledge-fabric/        # features/13_knowledge_fabric/
│   ├── evidence-service/        # features/14_evidence_and_provenance/
│   ├── artifact-engine/         # features/15_artifact_engine/
│   ├── approval-service/        # features/16_human_approval/
│   ├── audit-service/           # features/17_audit/
│   ├── network-monitor/         # features/18_network_sovereignty/
│   ├── identity-service/        # features/19_identity_and_rbac/
│   ├── policy-engine/           # features/20_data_classification/, 21_policy_engine/
│   ├── memory-service/          # features/22_agent_memory/
│   └── admin-console/           # features/24_admin_console/
├── packages/                    # Shared libraries, imported by services/ and apps/, never the reverse
│   ├── domain/                  # Entity types matching docs/domain/
│   ├── schemas/                 # Generated types from docs/schemas/*.json blocks
│   ├── error-registry/          # Generated from docs/reference/01_error_codes.md
│   ├── permission-matrix/       # Generated from docs/reference/05_permission_matrix.md
│   ├── retry-policy/            # Generated from docs/runtime/11_retry_policy.md
│   └── observability/           # Shared logging/metrics/tracing helpers, features/25_observability/
├── infra/
│   ├── docker/                  # Per-service Dockerfiles
│   ├── compose/                 # docker-compose.*.yml per deployment/ profile
│   └── migrations/              # Forward-only SQL migrations, see schemas/01_database_schema.md
├── tests/
│   ├── unit/                    # mirrors services/ and packages/ structure
│   ├── integration/
│   ├── security/                # SEC-TEST-### implementations, testing/21_security_testing.md
│   └── e2e/                     # TEST-E2E-### implementations, demo/ scenarios
└── docs/                        # this specification tree
```

## Dependency direction

`apps/` → `services/` (via API only, never direct imports) → `packages/`. `services/*`
may import `packages/*` but never import from another `services/*` directly — cross-service
calls go through the API layer or an internal message/queue, never a shared code import. This
prevents the circular-dependency risk called out in the Upgrade Prompt §35.

`packages/*` never import from `services/*` or `apps/*` — the dependency graph is strictly
one-directional, matching `10_DEPENDENCY_GRAPH.md`.
