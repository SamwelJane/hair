import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.external_shipments import ExternalShipment
    from app.models.identity import User
    from app.models.orders import Order
    from app.models.packages import Package


class TrackingEvent(Base, UUIDPrimaryKeyMixin):
    """The unified customer-facing timeline (spec section 25/57) - replaces
    the old per-order ShipmentMilestone. Append-only: current state always
    lives on the owning Order/Package/Consolidation's own status field, this
    is only the narrative history for support/dispute resolution and the
    public tracking page. At least one owner must be set; a platform order
    can have order-level events before any Package exists (e.g. once Phase 9
    wires up "Order Placed"/"Payment Confirmed"), while an external shipment
    always has a Package from the moment it's created (see
    services/external_shipments.py)."""

    __tablename__ = "tracking_events"
    __table_args__ = (
        CheckConstraint(
            "order_id IS NOT NULL OR external_shipment_id IS NOT NULL OR package_id IS NOT NULL",
            name="ck_tracking_events_has_owner",
        ),
    )

    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    external_shipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_shipments.id"), nullable=True
    )
    package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order | None"] = relationship()
    external_shipment: Mapped["ExternalShipment | None"] = relationship()
    package: Mapped["Package | None"] = relationship()
    created_by: Mapped["User | None"] = relationship()
