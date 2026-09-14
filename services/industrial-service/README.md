# industrial-service

**Owner:** Character 4 — Industrial Intelligence

Implements the asset-centric industrial intelligence platform capabilities defined in
`docs/industrial/` and `docs/domain/20_asset_model.md`.

## What this service owns

- **Asset entity model** — Plant, Unit, Equipment, MaintenanceEvent, Inspection, Incident
  (PostgreSQL tables, matching `docs/domain/20_asset_model.md`)
- **Asset-centric knowledge graph** — the `governed_by` join table and entity-resolution
  logic (`docs/industrial/13_asset_knowledge_graph.md`)
- **Revision comparison / change detection** (`docs/industrial/05_document_comparison.md`,
  `06_change_detection.md`)
- **Knowledge conflict detection** (`docs/industrial/14_knowledge_conflict_detection.md`)
- **Industrial workflow handlers** — inspection report extraction, maintenance record
  extraction, SOP compliance checking (`docs/industrial/02–04_*.md`)

## What this service does NOT own

- OCR, chunking, embedding — those live in `services/document-pipeline/` and
  `services/knowledge-fabric/` (Character 3).
- Evidence rows — created via `services/evidence-service/` API (Character 3). This service
  reads Evidence to detect conflicts; it never writes Evidence tables directly.
- Artifact rows — read from `services/artifact-engine/` API (Character 6).
- Authentication, RBAC, audit — every handler calls `packages/permission-matrix/` checks and
  writes an AuditEvent via the audit-service API; it does not own those systems.

## Stack

- Python 3.11, FastAPI, asyncpg (PostgreSQL 15+)
- Deterministic calculation helpers in `app/calculations.py`
  (`docs/industrial/10_engineering_calculations.md`): tolerance checks, explicit
  unit conversions, aggregate statistics. These run locally today with full input
  traceability so callers can cite inputs as Evidence; when Character 2's
  Calculator Tool (`services/tool-gateway/`, `features/07_calculator_tool/`) is
  available, `/internal/verify-calculation` callers should cite its
  ToolInvocation instead — this service never asserts a numeric claim without
  an auditable computation behind it either way.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8005
```

## Testing

```bash
pip install -r requirements-test.txt
python -m pytest tests/ -q
python -m pytest tests/ -q --cov=app --cov-report=term-missing  # 100% line coverage
```

`tests/test_integration.py` runs against real PostgreSQL via embedded
`pgserver` (no external DB needed) and skips automatically when unavailable.

## Environment variables

See `docs/16_ENVIRONMENT_AND_CONFIGURATION.md` for the full list. Minimum required:

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sovereign
CALCULATOR_TOOL_URL=http://tool-gateway:8003/tools/calculator
EVIDENCE_SERVICE_URL=http://evidence-service:8004
AUDIT_SERVICE_URL=http://audit-service:8006
```
