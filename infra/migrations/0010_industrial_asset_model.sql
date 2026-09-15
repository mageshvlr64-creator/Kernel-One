-- Migration: 0010_industrial_asset_model.sql
-- Owner: Character 4 — Industrial Intelligence
-- Source: docs/domain/20_asset_model.md, docs/industrial/13_asset_knowledge_graph.md
--
-- Forward-only migration.  Never edit a deployed migration — add a new one.
-- Run via: psql $DATABASE_URL -f this_file.sql

BEGIN;

-- Plants
CREATE TABLE IF NOT EXISTS plants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    name            TEXT NOT NULL,
    location        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);

COMMENT ON TABLE  plants                IS 'Top-level physical facility. docs/domain/20_asset_model.md.';
COMMENT ON COLUMN plants.organization_id IS 'FK → organizations.id (owned by Character 1 domain)';
COMMENT ON COLUMN plants.location        IS 'Free text; not geocoded in V1.';
COMMENT ON COLUMN plants.deleted_at      IS 'Soft-delete timestamp; NULL = active.';

-- Units
CREATE TABLE IF NOT EXISTS units (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plant_id    UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    unit_type   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

COMMENT ON TABLE  units           IS 'Process unit within a Plant. docs/domain/20_asset_model.md.';
COMMENT ON COLUMN units.unit_type IS 'Free text, e.g. "distillation", "utilities".';

-- Equipment
CREATE TABLE IF NOT EXISTS equipment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id         UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    tag_number      TEXT NOT NULL,
    name            TEXT NOT NULL,
    equipment_type  TEXT,
    manufacturer    TEXT,
    model_number    TEXT,
    status          TEXT NOT NULL DEFAULT 'operational'
                        CHECK (status IN ('operational','degraded','down','decommissioned')),
    commissioned_at DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,
    UNIQUE (unit_id, tag_number)
);

COMMENT ON TABLE  equipment            IS 'Physical equipment item. docs/domain/20_asset_model.md.';
COMMENT ON COLUMN equipment.tag_number IS 'Unique within unit_id; used for entity resolution during ingestion.';
COMMENT ON COLUMN equipment.status     IS 'Operator-set; NOT auto-derived from inspection findings (principle 6).';

-- MaintenanceEvents
CREATE TABLE IF NOT EXISTS maintenance_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,
    event_type          TEXT,
    performed_at        DATE,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  maintenance_events                   IS 'docs/domain/20_asset_model.md, docs/industrial/03_maintenance_records.md.';
COMMENT ON COLUMN maintenance_events.source_document_id IS 'FK → documents.id (Character 3); the maintenance record this was extracted from.';

-- Inspections
CREATE TABLE IF NOT EXISTS inspections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,
    inspected_at        DATE,
    finding_summary     TEXT,
    severity            TEXT CHECK (severity IN ('informational','minor','major','critical')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  inspections                   IS 'docs/domain/20_asset_model.md, docs/industrial/02_inspection_reports.md.';
COMMENT ON COLUMN inspections.source_document_id IS 'FK → documents.id (Character 3); the inspection report this was extracted from.';

-- Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,
    occurred_at         DATE,
    description         TEXT,
    severity            TEXT CHECK (severity IN ('informational','minor','major','critical')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE incidents IS 'docs/domain/20_asset_model.md.';

-- governed_by join table: Equipment ↔ Document (many-to-many)
-- docs/industrial/13_asset_knowledge_graph.md
CREATE TABLE IF NOT EXISTS equipment_governing_documents (
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    document_id         UUID NOT NULL,
    relationship_note   TEXT,
    PRIMARY KEY (equipment_id, document_id)
);

COMMENT ON TABLE  equipment_governing_documents                  IS 'governed_by edges. docs/industrial/13_asset_knowledge_graph.md.';
COMMENT ON COLUMN equipment_governing_documents.document_id       IS 'FK → documents.id (Character 3). Not a FK constraint because documents live in a separate service boundary.';
COMMENT ON COLUMN equipment_governing_documents.relationship_note IS 'e.g. "operating procedure", "lockout-tagout procedure".';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_plants_org          ON plants(organization_id)             WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_units_plant         ON units(plant_id)                     WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_equipment_unit      ON equipment(unit_id)                  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_equipment_tag       ON equipment(tag_number)               WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_maintenance_equip   ON maintenance_events(equipment_id);
CREATE INDEX IF NOT EXISTS idx_inspections_equip   ON inspections(equipment_id);
CREATE INDEX IF NOT EXISTS idx_inspections_date    ON inspections(equipment_id, inspected_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_equip     ON incidents(equipment_id);
CREATE INDEX IF NOT EXISTS idx_gov_docs_equip      ON equipment_governing_documents(equipment_id);
CREATE INDEX IF NOT EXISTS idx_gov_docs_document   ON equipment_governing_documents(document_id);

COMMIT;
