"""Phase 2 (domain model) coverage: the new tables exist, their unique
constraints hold, and the CHECK constraints that encode "exactly one owner"
rules are enforced at the database level - not just by convention. The
warehouse/consolidation/customs *workflows* (state transitions, receiving,
QC, etc.) are service-layer work for later phases and have no service to
test yet."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.consolidation import Consolidation
from app.models.customs import CustomsDeclaration
from app.models.enums import ConsolidationStatus, WarehouseType
from app.models.exceptions import OpsException
from app.models.external_shipments import ExternalShipment
from app.models.packages import Package
from app.models.warehouse import Warehouse
from tests.integration.conftest import checkout_payload


async def _make_warehouse(db, *, code="CHERUBIM-VN", type_=WarehouseType.VN) -> Warehouse:
    warehouse = Warehouse(code=code, name="Cherubim Express", type=type_, country="VN" if type_ == WarehouseType.VN else "KE")
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


async def _make_external_shipment(db, *, tracking_number="VNKE-EXT-20260916-000001") -> ExternalShipment:
    shipment = ExternalShipment(tracking_number=tracking_number, customer_name="Jane Doe", customer_phone="+254700000001")
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return shipment


async def test_warehouse_code_must_be_unique(db):
    await _make_warehouse(db)
    db.add(Warehouse(code="CHERUBIM-VN", name="Duplicate", type=WarehouseType.VN, country="VN"))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_external_shipment_tracking_number_must_be_unique(db):
    await _make_external_shipment(db)
    db.add(ExternalShipment(tracking_number="VNKE-EXT-20260916-000001", customer_name="Other", customer_phone="+254700000002"))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_package_can_belong_to_external_shipment_only(db):
    warehouse = await _make_warehouse(db)
    shipment = await _make_external_shipment(db)

    package = Package(package_code="PKG-000001", external_shipment_id=shipment.id, warehouse_id=warehouse.id)
    db.add(package)
    await db.commit()
    await db.refresh(package)

    assert package.order_id is None
    assert package.status.value == "EXPECTED"
    assert package.qc_status.value == "PENDING"


async def test_package_rejects_both_owners_set(db, admin_user, checkout_fixtures, client):
    order_number = (
        await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))
    ).json()["order_number"]
    from sqlalchemy import select

    from app.models.orders import Order

    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    shipment = await _make_external_shipment(db)

    db.add(Package(package_code="PKG-000002", order_id=order.id, external_shipment_id=shipment.id))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_package_rejects_no_owner_set(db):
    db.add(Package(package_code="PKG-000003"))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_consolidation_groups_packages(db):
    vn_warehouse = await _make_warehouse(db)
    ke_warehouse = await _make_warehouse(db, code="KE-MAIN", type_=WarehouseType.KE)
    shipment = await _make_external_shipment(db)

    consolidation = Consolidation(
        consolidation_code="CON-VN-20260916-0001",
        origin_warehouse_id=vn_warehouse.id,
        destination_warehouse_id=ke_warehouse.id,
        status=ConsolidationStatus.OPEN,
    )
    db.add(consolidation)
    await db.flush()

    package = Package(
        package_code="PKG-000004",
        external_shipment_id=shipment.id,
        warehouse_id=vn_warehouse.id,
        consolidation_id=consolidation.id,
    )
    db.add(package)
    await db.commit()
    await db.refresh(consolidation, attribute_names=["packages"])

    assert len(consolidation.packages) == 1
    assert consolidation.packages[0].package_code == "PKG-000004"


async def test_customs_declaration_requires_consolidation_or_package(db):
    db.add(CustomsDeclaration(duty_usd=Decimal(0), vat_usd=Decimal(0)))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_customs_declaration_linked_to_consolidation(db):
    warehouse = await _make_warehouse(db)
    consolidation = Consolidation(consolidation_code="CON-VN-20260916-0002", origin_warehouse_id=warehouse.id)
    db.add(consolidation)
    await db.flush()

    declaration = CustomsDeclaration(consolidation_id=consolidation.id, duty_usd=Decimal("12.50"), vat_usd=Decimal("8.00"))
    db.add(declaration)
    await db.commit()
    await db.refresh(declaration)

    assert declaration.status.value == "PREPARING"


async def test_ops_exception_polymorphic_reference(db):
    warehouse = await _make_warehouse(db)
    exception = OpsException(
        type="PACKAGE_DAMAGED",
        entity_type="Warehouse",
        entity_id=str(warehouse.id),
        description="Forklift dropped a pallet.",
    )
    db.add(exception)
    await db.commit()
    await db.refresh(exception)

    assert exception.severity.value == "MEDIUM"
    assert exception.status.value == "OPEN"


async def test_order_tracking_number_is_unique_at_the_database_level(db, admin_user, checkout_fixtures, client):
    """The generator (tests/unit/test_tracking_numbering.py) already avoids
    collisions - this just confirms the DB would actually reject one if it
    ever happened, e.g. from a future code path that bypasses the
    generator."""
    order_number = (
        await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))
    ).json()["order_number"]
    from sqlalchemy import select

    from app.models.orders import Order

    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    assert order.tracking_number.startswith("VNKE-")

    order_number_2 = (
        await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))
    ).json()["order_number"]
    order_2 = (await db.execute(select(Order).where(Order.order_number == order_number_2))).scalar_one()
    order_2.tracking_number = order.tracking_number
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()
