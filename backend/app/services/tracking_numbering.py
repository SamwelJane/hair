from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_shipments import ExternalShipment
from app.models.orders import Order
from app.services.order_numbering import random_suffix


class TrackingNumberGenerationError(Exception):
    pass


async def _is_taken(db: AsyncSession, candidate: str) -> bool:
    # Order and ExternalShipment tracking numbers share one namespace even
    # though their prefixes (VNKE- vs VNKE-EXT-) can't actually collide as
    # strings today - checking both tables keeps that a property of this
    # function rather than an assumption callers have to know about.
    order_hit = await db.scalar(select(Order.id).where(Order.tracking_number == candidate))
    if order_hit is not None:
        return True
    external_hit = await db.scalar(select(ExternalShipment.id).where(ExternalShipment.tracking_number == candidate))
    return external_hit is not None


async def generate_order_tracking_number(db: AsyncSession) -> str:
    """Generates the immutable, customer-facing tracking number for a
    platform order - created once at order-creation time (see
    routers/orders.py::checkout) and never regenerated afterwards, including
    when a warehouse later receives/labels/reprints the corresponding
    package (see docs/VNKE_ROADMAP.md Phase 3/5)."""
    date_part = datetime.now(UTC).strftime("%Y%m%d")

    for _ in range(5):
        candidate = f"VNKE-{date_part}-{random_suffix(6)}"
        if not await _is_taken(db, candidate):
            return candidate

    raise TrackingNumberGenerationError("Failed to generate a unique tracking number after 5 attempts.")


async def generate_external_shipment_tracking_number(db: AsyncSession) -> str:
    """Generates the immutable tracking number for a shipment bought outside
    the platform - created once when warehouse staff create the
    ExternalShipment record, never regenerated afterwards."""
    date_part = datetime.now(UTC).strftime("%Y%m%d")

    for _ in range(5):
        candidate = f"VNKE-EXT-{date_part}-{random_suffix(6)}"
        if not await _is_taken(db, candidate):
            return candidate

    raise TrackingNumberGenerationError("Failed to generate a unique tracking number after 5 attempts.")
