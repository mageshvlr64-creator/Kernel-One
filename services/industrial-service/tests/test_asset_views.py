import uuid
from datetime import datetime, timezone

from app.models import EquipmentStatus, MaintenanceEventCreate


def _equipment(**kwargs):
    from app.models import Equipment

    base = {
        "id": uuid.uuid4(),
        "unit_id": uuid.uuid4(),
        "tag_number": "P-204",
        "name": "Feed Pump P-204",
        "status": EquipmentStatus.operational,
        "created_at": datetime.now(timezone.utc),
        "deleted_at": None,
    }
    base.update(kwargs)
    return Equipment(**base)


def test_maintenance_event_technician_fields_optional():
    m = MaintenanceEventCreate(equipment_id=uuid.uuid4())
    assert m.technician is None and m.work_order_id is None
    m2 = MaintenanceEventCreate(
        equipment_id=uuid.uuid4(), technician="J. Doe", work_order_id="WO-118"
    )
    assert m2.technician == "J. Doe" and m2.work_order_id == "WO-118"


def test_asset_list_item_shape():
    from app.main import AssetListItem

    item = AssetListItem(
        equipment=_equipment(), unit_name="CDU-2", last_inspection_date=None
    )
    assert item.unit_name == "CDU-2"
    assert item.last_inspection_date is None


def test_asset_detail_includes_resolutions():
    from app.main import AssetDetail

    detail = AssetDetail(equipment=_equipment())
    assert detail.conflict_resolutions == []
    assert detail.maintenance_events == []
