from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.enums import PackageStatus
from app.models.external_shipments import ExternalShipment
from app.models.orders import Order
from app.models.packages import Package
from app.models.tracking_events import TrackingEvent
from app.schemas.tracking import (
    DeliveryEstimateOut,
    PublicTrackingOut,
    TrackingEventOut,
    TrackingPackageOut,
)
from app.services.shipping_estimator import get_delivery_estimate

router = APIRouter(tags=["tracking"])

# Least-advanced-package-wins ordering for the combined status shown on a
# multi-package order (spec section 56: "the overall order page should
# summarize the combined state"). EXCEPTION is handled separately since it
# always needs attention regardless of where other packages are.
_PACKAGE_PROGRESSION = [
    PackageStatus.EXPECTED,
    PackageStatus.RECEIVED,
    PackageStatus.READY_FOR_CONSOLIDATION,
    PackageStatus.CONSOLIDATED,
    PackageStatus.IN_TRANSIT,
    PackageStatus.AT_CUSTOMS_KENYA,
    PackageStatus.READY_FOR_DELIVERY,
    PackageStatus.DELIVERED,
]


def _combined_status(order: Order | None, packages: list[Package]) -> str:
    if any(p.status == PackageStatus.EXCEPTION for p in packages):
        return PackageStatus.EXCEPTION.value
    if not packages:
        # Only possible for a platform order with no package received yet -
        # an external shipment always has one from the moment it's created.
        return order.status.value if order else PackageStatus.RECEIVED.value
    least_advanced = min(packages, key=lambda p: _PACKAGE_PROGRESSION.index(p.status))
    return least_advanced.status.value


@router.get("/track/{tracking_number}", response_model=PublicTrackingOut)
async def track_shipment(tracking_number: str, db: AsyncSession = Depends(get_db)) -> PublicTrackingOut:
    order = await db.scalar(select(Order).where(Order.tracking_number == tracking_number))
    external_shipment = None
    if order is None:
        external_shipment = await db.scalar(
            select(ExternalShipment).where(ExternalShipment.tracking_number == tracking_number)
        )
    if order is None and external_shipment is None:
        raise HTTPException(status_code=404, detail="Tracking number not found.")

    if order is not None:
        packages = (await db.execute(select(Package).where(Package.order_id == order.id))).scalars().all()
    else:
        assert external_shipment is not None  # guaranteed by the 404 check above
        packages = (
            (await db.execute(select(Package).where(Package.external_shipment_id == external_shipment.id)))
            .scalars()
            .all()
        )

    event_conditions: list[ColumnElement[bool]] = (
        [TrackingEvent.package_id.in_([p.id for p in packages])] if packages else []
    )
    if order is not None:
        event_conditions.append(TrackingEvent.order_id == order.id)
    if external_shipment is not None:
        event_conditions.append(TrackingEvent.external_shipment_id == external_shipment.id)
    events = (
        (await db.execute(select(TrackingEvent).where(or_(*event_conditions)).order_by(TrackingEvent.occurred_at)))
        .scalars()
        .all()
        if event_conditions
        else []
    )

    delivery_estimate = None
    if order is not None:
        estimate = await get_delivery_estimate(db, order.shipping_country)
        if estimate is not None:
            delivery_estimate = DeliveryEstimateOut(min_days=estimate.min_days, max_days=estimate.max_days)

    return PublicTrackingOut(
        tracking_number=tracking_number,
        status=_combined_status(order, list(packages)),
        packages=[TrackingPackageOut(package_code=p.package_code, status=p.status.value, qc_status=p.qc_status.value) for p in packages],
        events=[
            TrackingEventOut(id=e.id, label=e.label, location=e.location, note=e.note, occurred_at=e.occurred_at)
            for e in events
        ],
        delivery_estimate=delivery_estimate,
    )
