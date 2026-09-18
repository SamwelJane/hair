import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracking_events import TrackingEvent


async def add_event(
    db: AsyncSession,
    *,
    order_id: uuid.UUID | None = None,
    external_shipment_id: uuid.UUID | None = None,
    package_id: uuid.UUID | None = None,
    label: str,
    location: str | None = None,
    note: str | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> TrackingEvent:
    """Does not commit - composes into the caller's existing transaction
    (every call site already commits once at the end of its own service
    function)."""
    event = TrackingEvent(
        order_id=order_id,
        external_shipment_id=external_shipment_id,
        package_id=package_id,
        label=label,
        location=location,
        note=note,
        created_by_id=actor_user_id,
    )
    db.add(event)
    await db.flush()
    return event
