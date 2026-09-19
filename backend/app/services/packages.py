import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.enums import (
    OpsExceptionSeverity,
    OpsExceptionStatus,
    OpsExceptionType,
    PackageCondition,
    PackageQCStatus,
    PackageStatus,
    WarehouseType,
)
from app.models.exceptions import OpsException
from app.models.external_shipments import ExternalShipment
from app.models.orders import Order
from app.models.packages import Package
from app.models.payments import SupplierOrder
from app.models.warehouse import Warehouse
from app.services.audit import log_audit
from app.services.notifications.whatsapp import (
    customer_package_received_whatsapp_message,
    send_whatsapp,
)
from app.services.order_numbering import random_suffix
from app.services.tracking_events import add_event

settings = get_settings()


class TrackingNumberNotFoundError(Exception):
    pass


class InvalidSupplierOrderError(Exception):
    pass


class DuplicateReceiptError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class LabelAlreadyPrintedError(Exception):
    pass


class LabelNotYetPrintedError(Exception):
    pass


async def resolve_tracking_numbers_batch(db: AsyncSession, packages: list[Package]) -> dict[uuid.UUID, str]:
    """Batched form of resolve_tracking_number, for the two views that
    render a whole list of packages at once (the registry and a
    consolidation's contents) - calling resolve_tracking_number once per
    package there was an N+1 query (up to PAGE_SIZE extra round-trips per
    request), found during the Phase 12 performance review."""
    order_ids = {p.order_id for p in packages if p.order_id is not None}
    shipment_ids = {p.external_shipment_id for p in packages if p.external_shipment_id is not None}

    tracking_by_order_id: dict[uuid.UUID, str] = {}
    if order_ids:
        rows = (await db.execute(select(Order.id, Order.tracking_number).where(Order.id.in_(order_ids)))).all()
        tracking_by_order_id = {order_id: tracking_number for order_id, tracking_number in rows}

    tracking_by_shipment_id: dict[uuid.UUID, str] = {}
    if shipment_ids:
        rows = (
            await db.execute(
                select(ExternalShipment.id, ExternalShipment.tracking_number).where(
                    ExternalShipment.id.in_(shipment_ids)
                )
            )
        ).all()
        tracking_by_shipment_id = {shipment_id: tracking_number for shipment_id, tracking_number in rows}

    result: dict[uuid.UUID, str] = {}
    for package in packages:
        if package.order_id is not None:
            result[package.id] = tracking_by_order_id[package.order_id]
        else:
            assert package.external_shipment_id is not None
            result[package.id] = tracking_by_shipment_id[package.external_shipment_id]
    return result


async def resolve_tracking_number(db: AsyncSession, package: Package) -> str:
    """Shared by every warehouse view that renders a *single* package (the
    detail page, right after receive/qc/weigh mutations) - a package never
    has its own tracking number column, it always belongs to whichever
    Order or ExternalShipment generated one. For a list of packages, use
    resolve_tracking_numbers_batch instead to avoid an N+1 query."""
    if package.order_id is not None:
        order = await db.get(Order, package.order_id)
        assert order is not None
        return order.tracking_number
    shipment = await db.get(ExternalShipment, package.external_shipment_id)
    assert shipment is not None
    return shipment.tracking_number


def compute_volume_cbm(length_cm: Decimal | None, width_cm: Decimal | None, height_cm: Decimal | None) -> Decimal | None:
    if length_cm is None or width_cm is None or height_cm is None:
        return None
    return (length_cm * width_cm * height_cm) / Decimal(1_000_000)


def mask_customer_name(full_name: str) -> str:
    """'Jane Doe' -> 'Jane D.' - full names must never appear on a physical
    warehouse label (spec section 45)."""
    parts = full_name.strip().split()
    if not parts:
        return "Customer"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


async def generate_package_code(db: AsyncSession) -> str:
    for _ in range(5):
        candidate = f"PKG-{random_suffix(8)}"
        existing = await db.scalar(select(Package.id).where(Package.package_code == candidate))
        if existing is None:
            return candidate
    raise RuntimeError("Failed to generate a unique package code after 5 attempts.")


async def get_primary_vn_warehouse(db: AsyncSession) -> Warehouse:
    warehouse = await db.scalar(
        select(Warehouse)
        .where(Warehouse.type == WarehouseType.VN, Warehouse.is_active.is_(True))
        .order_by(Warehouse.created_at)
    )
    if warehouse is None:
        raise RuntimeError("No active Vietnam warehouse configured - see the 'seed cherubim vietnam warehouse' migration.")
    return warehouse


async def receive_platform_package(
    db: AsyncSession,
    *,
    tracking_number: str,
    supplier_order_id: uuid.UUID | None,
    weight_grams: int | None,
    condition: PackageCondition | None,
    notes: str | None,
    actor_user_id: uuid.UUID,
) -> Package:
    """Scans an *existing* order tracking number and creates the Package row
    for its physical arrival - never generates a new tracking number (spec
    section 5: "Staff must NOT generate another tracking number").

    Weight workflow:
    - Warehouse always enters weight in grams (no CBM/dimensions required).
    - weight_kg is computed automatically: weight_grams / 1000.
    - If supplier declared a total weight for their items, a >10% variance
      triggers an automatic WEIGHT_MISMATCH OpsException for ops review.
    """
    order = await db.scalar(
        select(Order).where(Order.tracking_number == tracking_number).options(selectinload(Order.user))
    )
    if order is None:
        raise TrackingNumberNotFoundError(f"Tracking number {tracking_number} not found.")

    supplier_order = None
    if supplier_order_id is not None:
        supplier_order = await db.get(SupplierOrder, supplier_order_id)
        if supplier_order is None or supplier_order.order_id != order.id:
            raise InvalidSupplierOrderError("Supplier order does not belong to this tracking number's order.")

    # One package per (order, supplier_order) pair - a repeat scan of the
    # same tracking number/supplier combination is a duplicate receipt, not
    # a second physical package.
    existing = await db.scalar(
        select(Package.id).where(Package.order_id == order.id, Package.supplier_order_id == supplier_order_id)
    )
    if existing is not None:
        raise DuplicateReceiptError("This package has already been received.")

    # Grams → kg conversion (warehouse enters grams; pricing/shipping uses kg)
    weight_kg: Decimal | None = None
    if weight_grams is not None:
        weight_kg = (Decimal(weight_grams) / Decimal(1000)).quantize(Decimal("0.001"))

    warehouse = await get_primary_vn_warehouse(db)
    package = Package(
        package_code=await generate_package_code(db),
        order_id=order.id,
        supplier_order_id=supplier_order_id,
        warehouse_id=warehouse.id,
        weight_grams=weight_grams,
        weight_kg=weight_kg,
        condition=condition,
        notes=notes,
        status=PackageStatus.RECEIVED,
        received_at=datetime.now(UTC),
        received_by_id=actor_user_id,
    )
    db.add(package)
    await db.flush()

    # ── Weight discrepancy check ─────────────────────────────────────────────
    # Compare actual weighed grams against the sum of supplier-declared weights
    # for all items in this supplier's portion of the order. A >10% variance
    # auto-raises a WEIGHT_MISMATCH so ops staff can flag it with the factory.
    if weight_grams is not None and supplier_order is not None:
        from app.models.catalog import Product, ProductVariant
        from app.models.orders import OrderItem

        # Load items that belong to this supplier's order
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .options(
                selectinload(OrderItem.product),
                selectinload(OrderItem.variant),
            )
        )
        items = list((await db.execute(stmt)).scalars().all())
        supplier_items = [i for i in items if i.product.supplier_id == supplier_order.supplier_id]

        # Sum declared weights: prefer variant-level override, then product-level.
        # Both are stored in grams.
        declared_grams: int = 0
        all_declared = True
        for item in supplier_items:
            item_weight = None
            if item.variant is not None and item.variant.weight_override_grams is not None:
                item_weight = item.variant.weight_override_grams
            elif item.product.base_weight_grams is not None:
                item_weight = item.product.base_weight_grams
            if item_weight is None:
                all_declared = False
                break
            declared_grams += item_weight * item.quantity

        if all_declared and declared_grams > 0:
            variance_pct = Decimal(abs(weight_grams - declared_grams)) / Decimal(declared_grams)
            if variance_pct > Decimal("0.10"):
                db.add(
                    OpsException(
                        type=OpsExceptionType.WEIGHT_MISMATCH,
                        severity=OpsExceptionSeverity.MEDIUM,
                        entity_type="Package",
                        entity_id=str(package.id),
                        description=(
                            f"Weight mismatch: warehouse scanned {weight_grams}g, "
                            f"supplier declared {declared_grams}g "
                            f"({variance_pct * 100:.1f}% variance)."
                        ),
                        status=OpsExceptionStatus.OPEN,
                    )
                )

    await add_event(
        db,
        order_id=order.id,
        package_id=package.id,
        label="Received at Cherubim Warehouse",
        location="Vietnam",
        actor_user_id=actor_user_id,
    )
    await log_audit(
        db,
        user_id=actor_user_id,
        action="RECEIVE_PACKAGE",
        entity_type="Package",
        entity_id=str(package.id),
        metadata={
            "trackingNumber": tracking_number,
            "orderId": str(order.id),
            "weightGrams": weight_grams,
            "weightKg": str(weight_kg) if weight_kg is not None else None,
        },
    )
    await db.commit()
    await db.refresh(package)

    customer_phone = None
    if isinstance(order.shipping_address, dict):
        customer_phone = order.shipping_address.get("phone")
    if not customer_phone and order.user:
        customer_phone = order.user.phone

    if customer_phone:
        await send_whatsapp(
            customer_phone,
            customer_package_received_whatsapp_message(order_number=order.order_number, tracking_number=tracking_number),
        )

    return package



async def run_qc(
    db: AsyncSession,
    *,
    package_id: uuid.UUID,
    qc_status: PackageQCStatus,
    condition: PackageCondition | None,
    notes: str | None,
    actor_user_id: uuid.UUID,
) -> Package:
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")

    package.qc_status = qc_status
    if condition is not None:
        package.condition = condition
    if notes is not None:
        package.notes = notes

    if qc_status == PackageQCStatus.FAILED:
        package.status = PackageStatus.EXCEPTION
        db.add(
            OpsException(
                type=OpsExceptionType.QC_FAILURE,
                severity=OpsExceptionSeverity.MEDIUM,
                entity_type="Package",
                entity_id=str(package.id),
                description=notes or "QC failed.",
                status=OpsExceptionStatus.OPEN,
            )
        )
    elif qc_status == PackageQCStatus.PASSED and package.status == PackageStatus.RECEIVED:
        package.status = PackageStatus.READY_FOR_CONSOLIDATION
        await add_event(db, package_id=package.id, label="Package Verified", actor_user_id=actor_user_id)

    await log_audit(
        db,
        user_id=actor_user_id,
        action="PACKAGE_QC",
        entity_type="Package",
        entity_id=str(package.id),
        metadata={"qcStatus": qc_status.value, "condition": condition.value if condition else None},
    )
    await db.commit()
    await db.refresh(package)
    return package


async def record_weight(
    db: AsyncSession,
    *,
    package_id: uuid.UUID,
    weight_grams: int,
    actor_user_id: uuid.UUID,
) -> Package:
    """Records the weighed mass for a package. Warehouse enters grams; kg is
    derived automatically. No CBM/dimension capture — platform charges by
    weight ($60/kg), not volumetric rate."""
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")

    package.weight_grams = weight_grams
    package.weight_kg = (Decimal(weight_grams) / Decimal(1000)).quantize(Decimal("0.001"))

    await log_audit(
        db,
        user_id=actor_user_id,
        action="PACKAGE_WEIGH",
        entity_type="Package",
        entity_id=str(package.id),
        metadata={"weightGrams": weight_grams, "weightKg": str(package.weight_kg)},
    )
    await db.commit()
    await db.refresh(package)
    return package


async def add_package_photo(db: AsyncSession, *, package_id: uuid.UUID, photo_url: str, actor_user_id: uuid.UUID) -> Package:
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")

    package.photo_urls = [*(package.photo_urls or []), photo_url]

    await log_audit(
        db, user_id=actor_user_id, action="PACKAGE_PHOTO_ADDED", entity_type="Package", entity_id=str(package.id), metadata={}
    )
    await db.commit()
    await db.refresh(package)
    return package


async def _resolve_label_context(db: AsyncSession, package: Package) -> tuple[str, str, str]:
    """Returns (tracking_number, masked_customer_name, destination)."""
    if package.order_id is not None:
        order = await db.get(Order, package.order_id, options=[selectinload(Order.user)])
        assert order is not None  # guaranteed by the CHECK constraint + FK
        address = order.shipping_address or {}
        city = address.get("city")
        destination = f"{city}, {order.shipping_country}" if city else order.shipping_country
        return order.tracking_number, mask_customer_name(order.user.name), destination

    shipment = await db.get(ExternalShipment, package.external_shipment_id)
    assert shipment is not None
    return shipment.tracking_number, mask_customer_name(shipment.customer_name), "Kenya"


async def build_label(db: AsyncSession, package: Package) -> dict:
    tracking_number, masked_name, destination = await _resolve_label_context(db, package)
    return {
        "package_id": package.id,
        "package_code": package.package_code,
        "tracking_number": tracking_number,
        "masked_customer_name": masked_name,
        "destination": destination,
        "weight_grams": package.weight_grams,
        "qr_url": f"{settings.frontend_url}/track/{tracking_number}",
    }


async def print_label(db: AsyncSession, *, package_id: uuid.UUID, actor_user_id: uuid.UUID) -> Package:
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")
    if package.label_printed_at is not None:
        raise LabelAlreadyPrintedError("Label already printed for this package - use reprint instead.")

    package.label_printed_at = datetime.now(UTC)
    await log_audit(db, user_id=actor_user_id, action="PRINT_LABEL", entity_type="Package", entity_id=str(package.id), metadata={})
    await db.commit()
    await db.refresh(package)
    return package


async def reprint_label(db: AsyncSession, *, package_id: uuid.UUID, actor_user_id: uuid.UUID) -> Package:
    """Never mutates the tracking number and never creates a new Package -
    only increments a counter, so this is safe to call any number of times
    (spec section 13: "Reprinting MUST NOT generate a new tracking number")."""
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")
    if package.label_printed_at is None:
        raise LabelNotYetPrintedError("Label has not been printed yet - use print instead.")

    package.label_reprint_count += 1
    await log_audit(
        db,
        user_id=actor_user_id,
        action="REPRINT_LABEL",
        entity_type="Package",
        entity_id=str(package.id),
        metadata={"reprintCount": package.label_reprint_count},
    )
    await db.commit()
    await db.refresh(package)
    return package
