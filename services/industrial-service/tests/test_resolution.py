import uuid

from app.comparison import apply_table_confidence_default, compare_findings
from app.models import ConflictResolutionCreate, ConflictResolutionKind


def test_table_confidence_capped():
    assert apply_table_confidence_default(0.95, "table") == 0.6
    assert apply_table_confidence_default(0.4, "table") == 0.4


def test_prose_confidence_untouched():
    assert apply_table_confidence_default(0.95, "prose") == 0.95
    assert apply_table_confidence_default(0.95, None) == 0.95
    assert apply_table_confidence_default(None, "table") is None


def test_compare_caps_table_finding():
    a = uuid.uuid4()
    b = uuid.uuid4()
    diff = compare_findings(
        a,
        b,
        [{"parameter": "pressure", "value": "10", "confidence": 0.95}],
        [
            {
                "parameter": "pressure",
                "value": "12",
                "confidence": 0.95,
                "source_kind": "table",
            }
        ],
    )
    assert len(diff.changed) == 1
    assert diff.changed[0].confidence == 0.6


def test_resolution_kinds_valid():
    eid = uuid.uuid4()
    for kind in ("downgrade_authority", "set_effective_until", "acknowledge_both"):
        r = ConflictResolutionCreate(
            equipment_id=eid,
            claim_description="Filter interval",
            source_a_document_id=uuid.uuid4(),
            source_b_document_id=uuid.uuid4(),
            resolution_kind=ConflictResolutionKind(kind),
        )
        assert r.resolution_kind.value == kind
