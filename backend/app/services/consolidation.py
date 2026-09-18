import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consolidation import Consolidation
from app.models.customs import CustomsDeclaration
from app.models.enums import (
    ConsolidationStatus,
    CustomsStatus,
    OpsExceptionSeverity,
    OpsExceptionStatus,
    OpsExceptionType,
    PackageStatus,
)
from app.models.exceptions import OpsException
from app.models.packages import Package
from app.models.warehouse import Warehouse
from app.services.audit import log_audit
from app.services.order_numbering import random_suffix
from app.services.packages import get_primary_vn_warehouse
from app.services.tracking_events import add_event


class ConsolidationNotFoundError(Exception):
    pass


class WarehouseNotFoundError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class PackageNotEligibleError(Exception):
    pass


class PackageAlreadyAssignedError(Exception):
    pass


class ConsolidationNotOpenError(Exception):
    pass


class EmptyConsolidationError(Exception):
    pass


class InvalidConsolidationTransitionError(Exception):
    pass


async def generate_consolidation_code(db: AsyncSession, origin_country: str) -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    for _ in range(5):
        candidate = f"CON-{origin_country}-{date_part}-{random_suffix(4)}"
        existing = await db.scalar(select(Consolidation.id).where(Consolidation.consolidation_code == candidate))
        if existing is None:
            return candidate
    raise RuntimeError("Failed to generate a unique consolidation code after 5 attempts.")


async def generate_shipment_code(db: AsyncSession) -> str:
    for _ in range(5):
        candidate = f"SHP-VNKE-{random_suffix(6)}"
        existing = await db.scalar(select(Consolidation.id).where(Consolidation.shipment_code == candidate))
        if existing is None:
            return candidate
    raise RuntimeError("Failed to generate a unique shipment code after 5 attempts.")


async def _recompute_totals(db: AsyncSession, consolidation: Consolidation) -> None:
    packages = (
        await db.execute(select(Package).where(Package.consolidation_id == consolidation.id))
    ).scalars().all()
    consolidation.total_weight_grams = sum((p.weight_grams or 0) for p in packages)
    consolidation.total_volume_cbm = sum((p.volume_cbm for p in packages if p.volume_cbm is not None), Decimal(0))


async def create_consolidation(
    db: AsyncSession,
    *,
    origin_warehouse_id: uuid.UUID | None,
    destination_warehouse_id: uuid.UUID | None,
    freight_method: str | None,
    freight_provider: str | None,
    actor_user_id: uuid.UUID,
) -> Consolidation:
    origin: Warehouse
    if origin_warehouse_id is None:
        origin = await get_primary_vn_warehouse(db)
    else:
        found = await db.get(Warehouse, origin_warehouse_id)
        if found is None:
            raise WarehouseNotFoundError(f"Warehouse {origin_warehouse_id} not found.")
        origin = found
    if destination_warehouse_id is not None and await db.get(Warehouse, destination_warehouse_id) is None:
        raise WarehouseNotFoundError(f"Warehouse {destination_warehouse_id} not found.")

    consolidation = Consolidation(
        consolidation_code=await generate_consolidation_code(db, origin.country),
        origin_warehouse_id=origin.id,
        destination_warehouse_id=destination_warehouse_id,
        freight_method=freight_method,
        freight_provider=freight_provider,
    )
    db.add(consolidation)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_CONSOLIDATION", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"originWarehouseId": str(origin.id)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def add_package(db: AsyncSession, *, consolidation_id: uuid.UUID, package_id: uuid.UUID, actor_user_id: uuid.UUID) -> Consolidation:
    consolidation = await db.get(Consolidation, consolidation_id)
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.OPEN:
        raise ConsolidationNotOpenError("This consolidation is no longer accepting packages.")

    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(f"Package {package_id} not found.")
    if package.consolidation_id is not None:
        raise PackageAlreadyAssignedError("This package is already assigned to a consolidation.")
    if package.status != PackageStatus.READY_FOR_CONSOLIDATION:
        raise PackageNotEligibleError(
            f"Package must have passed QC (status READY_FOR_CONSOLIDATION) - it is currently {package.status.value}."
        )

    package.consolidation_id = consolidation.id
    package.status = PackageStatus.CONSOLIDATED
    await db.flush()
    await _recompute_totals(db, consolidation)

    await add_event(
        db, package_id=package.id, label="Consolidated",
        note=f"Added to consolidation {consolidation.consolidation_code}", actor_user_id=actor_user_id,
    )
    await log_audit(
        db, user_id=actor_user_id, action="ADD_PACKAGE_TO_CONSOLIDATION", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"packageId": str(package.id)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def remove_package(db: AsyncSession, *, consolidation_id: uuid.UUID, package_id: uuid.UUID, actor_user_id: uuid.UUID) -> Consolidation:
    consolidation = await db.get(Consolidation, consolidation_id)
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.OPEN:
        raise ConsolidationNotOpenError("Packages cannot be removed once the consolidation is no longer open.")

    package = await db.get(Package, package_id)
    if package is None or package.consolidation_id != consolidation.id:
        raise PackageNotFoundError("This package is not part of this consolidation.")

    package.consolidation_id = None
    package.status = PackageStatus.READY_FOR_CONSOLIDATION
    await db.flush()
    await _recompute_totals(db, consolidation)

    await log_audit(
        db, user_id=actor_user_id, action="REMOVE_PACKAGE_FROM_CONSOLIDATION", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"packageId": str(package.id)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def mark_ready_for_export(db: AsyncSession, *, consolidation_id: uuid.UUID, actor_user_id: uuid.UUID) -> Consolidation:
    consolidation = await db.get(Consolidation, consolidation_id, options=[selectinload(Consolidation.packages)])
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.OPEN:
        raise InvalidConsolidationTransitionError(f"Cannot mark ready for export from status {consolidation.status.value}.")
    if not consolidation.packages:
        raise EmptyConsolidationError("Cannot mark an empty consolidation ready for export.")

    consolidation.status = ConsolidationStatus.READY_FOR_EXPORT
    await log_audit(
        db, user_id=actor_user_id, action="CONSOLIDATION_READY_FOR_EXPORT", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"packageCount": len(consolidation.packages)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def mark_departed(db: AsyncSession, *, consolidation_id: uuid.UUID, actor_user_id: uuid.UUID) -> Consolidation:
    """Locks the consolidation - packages already can't be added/removed once
    it leaves OPEN, but this is the point of no return for the batch itself
    (spec section 16: "A package already assigned to a closed/departed
    consolidation must not accidentally be added to another consolidation")."""
    consolidation = await db.get(Consolidation, consolidation_id, options=[selectinload(Consolidation.packages)])
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.READY_FOR_EXPORT:
        raise InvalidConsolidationTransitionError(f"Cannot mark departed from status {consolidation.status.value}.")

    consolidation.status = ConsolidationStatus.DEPARTED
    consolidation.departure_date = datetime.now(UTC)
    for package in consolidation.packages:
        package.status = PackageStatus.IN_TRANSIT
        await add_event(db, package_id=package.id, label="Departed Vietnam", actor_user_id=actor_user_id)

    await log_audit(
        db, user_id=actor_user_id, action="CONSOLIDATION_DEPARTED", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"packageCount": len(consolidation.packages)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def mark_in_transit(
    db: AsyncSession,
    *,
    consolidation_id: uuid.UUID,
    carrier: str | None,
    carrier_tracking_reference: str | None,
    current_location: str | None,
    actor_user_id: uuid.UUID,
) -> Consolidation:
    """Confirms the carrier has taken the batch and it's now formally an
    international shipment leg - generates the distinct SHP-VNKE-######
    identifier at this point (spec section 6), separate from the
    CON-VN-###### consolidation code used internally at the warehouse."""
    consolidation = await db.get(Consolidation, consolidation_id, options=[selectinload(Consolidation.packages)])
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.DEPARTED:
        raise InvalidConsolidationTransitionError(f"Cannot mark in transit from status {consolidation.status.value}.")

    consolidation.status = ConsolidationStatus.IN_TRANSIT
    consolidation.shipment_code = await generate_shipment_code(db)
    consolidation.carrier = carrier
    consolidation.carrier_tracking_reference = carrier_tracking_reference
    consolidation.current_location = current_location

    for package in consolidation.packages:
        await add_event(db, package_id=package.id, label="In Transit to Kenya", location=current_location, actor_user_id=actor_user_id)

    await log_audit(
        db, user_id=actor_user_id, action="CONSOLIDATION_IN_TRANSIT", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"shipmentCode": consolidation.shipment_code, "carrier": carrier},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def record_transit_update(
    db: AsyncSession,
    *,
    consolidation_id: uuid.UUID,
    current_location: str | None,
    estimated_arrival: datetime | None,
    actor_user_id: uuid.UUID,
) -> Consolidation:
    consolidation = await db.get(Consolidation, consolidation_id, options=[selectinload(Consolidation.packages)])
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.IN_TRANSIT:
        raise InvalidConsolidationTransitionError(f"Cannot record a transit update from status {consolidation.status.value}.")

    if current_location is not None:
        consolidation.current_location = current_location
    if estimated_arrival is not None:
        consolidation.estimated_arrival = estimated_arrival

    for package in consolidation.packages:
        await add_event(db, package_id=package.id, label="In Transit to Kenya", location=current_location, actor_user_id=actor_user_id)

    await log_audit(
        db, user_id=actor_user_id, action="CONSOLIDATION_TRANSIT_UPDATE", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"currentLocation": current_location},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def mark_arrived_kenya(db: AsyncSession, *, consolidation_id: uuid.UUID, actor_user_id: uuid.UUID) -> Consolidation:
    consolidation = await db.get(Consolidation, consolidation_id, options=[selectinload(Consolidation.packages)])
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")
    if consolidation.status != ConsolidationStatus.IN_TRANSIT:
        raise InvalidConsolidationTransitionError(f"Cannot mark arrived from status {consolidation.status.value}.")

    consolidation.status = ConsolidationStatus.ARRIVED
    consolidation.arrival_date = datetime.now(UTC)
    consolidation.current_location = "Kenya"

    for package in consolidation.packages:
        package.status = PackageStatus.AT_CUSTOMS_KENYA
        await add_event(db, package_id=package.id, label="Customs in Kenya", location="Kenya", actor_user_id=actor_user_id)

    # Gives Kenya ops a queue item to work from the moment a batch arrives,
    # rather than requiring a separate manual "start customs" step - see
    # docs/VNKE_ROADMAP.md Phase 7.
    db.add(CustomsDeclaration(consolidation_id=consolidation.id, status=CustomsStatus.PREPARING))

    await log_audit(
        db, user_id=actor_user_id, action="CONSOLIDATION_ARRIVED_KENYA", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"packageCount": len(consolidation.packages)},
    )
    await db.commit()
    await db.refresh(consolidation)
    return consolidation


async def report_exception(
    db: AsyncSession,
    *,
    consolidation_id: uuid.UUID,
    exception_type: OpsExceptionType,
    severity: OpsExceptionSeverity,
    description: str | None,
    actor_user_id: uuid.UUID,
) -> OpsException:
    """Logs an operational exception against a shipment/consolidation
    without necessarily changing its status - e.g. an arrival mismatch
    (fewer/more packages arrived than expected) still needs to be
    investigated, not silently auto-resolved (spec section 34)."""
    consolidation = await db.get(Consolidation, consolidation_id)
    if consolidation is None:
        raise ConsolidationNotFoundError(f"Consolidation {consolidation_id} not found.")

    exception = OpsException(
        type=exception_type,
        severity=severity,
        entity_type="Consolidation",
        entity_id=str(consolidation.id),
        description=description,
        status=OpsExceptionStatus.OPEN,
    )
    db.add(exception)

    await log_audit(
        db, user_id=actor_user_id, action="REPORT_CONSOLIDATION_EXCEPTION", entity_type="Consolidation",
        entity_id=str(consolidation.id), metadata={"exceptionType": exception_type.value, "severity": severity.value},
    )
    await db.commit()
    await db.refresh(exception)
    return exception
