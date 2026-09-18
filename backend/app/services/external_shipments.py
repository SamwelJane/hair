import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PackageStatus
from app.models.external_shipments import ExternalShipment
from app.models.packages import Package
from app.services.audit import log_audit
from app.services.packages import (
    compute_volume_cbm,
    generate_package_code,
    get_primary_vn_warehouse,
)
from app.services.tracking_events import add_event
from app.services.tracking_numbering import generate_external_shipment_tracking_number


async def create_external_shipment(
    db: AsyncSession,
    *,
    customer_name: str,
    customer_phone: str,
    customer_email: str | None,
    supplier_reference: str | None,
    notes: str | None,
    weight_grams: int | None,
    length_cm: Decimal | None,
    width_cm: Decimal | None,
    height_cm: Decimal | None,
    actor_user_id: uuid.UUID,
) -> tuple[ExternalShipment, Package]:
    """Warehouse staff intake for a shipment bought outside the platform -
    generates the tracking number and creates its first Package in one
    atomic step, mirroring the real single-screen intake workflow (spec
    section 12: enter customer/supplier/package details, generate tracking
    number, create package, all before printing the label)."""
    tracking_number = await generate_external_shipment_tracking_number(db)
    shipment = ExternalShipment(
        tracking_number=tracking_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        supplier_reference=supplier_reference,
        notes=notes,
        created_by_id=actor_user_id,
    )
    db.add(shipment)
    await db.flush()

    warehouse = await get_primary_vn_warehouse(db)
    package = Package(
        package_code=await generate_package_code(db),
        external_shipment_id=shipment.id,
        warehouse_id=warehouse.id,
        weight_grams=weight_grams,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        volume_cbm=compute_volume_cbm(length_cm, width_cm, height_cm),
        status=PackageStatus.RECEIVED,
        received_at=datetime.now(UTC),
        received_by_id=actor_user_id,
    )
    db.add(package)
    await db.flush()

    await add_event(
        db,
        external_shipment_id=shipment.id,
        package_id=package.id,
        label="Received at Cherubim Warehouse",
        location="Vietnam",
        actor_user_id=actor_user_id,
    )
    await log_audit(
        db,
        user_id=actor_user_id,
        action="CREATE_EXTERNAL_SHIPMENT",
        entity_type="ExternalShipment",
        entity_id=str(shipment.id),
        metadata={"trackingNumber": tracking_number, "customerPhone": customer_phone},
    )
    await db.commit()
    await db.refresh(shipment)
    await db.refresh(package)
    return shipment, package
