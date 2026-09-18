import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import ConsolidationStatus

if TYPE_CHECKING:
    from app.models.packages import Package
    from app.models.warehouse import Warehouse


class Consolidation(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """A freight batch grouping multiple Packages into one international
    shipment leg. Totals are recomputed by the service layer whenever
    packages are added/removed - not database-derived columns, since they
    need to be readable without a join in list views.

    Also plays the role of the spec's separate "InternationalShipment"
    entity once it departs (shipment_code/carrier/carrier_tracking_reference/
    current_location, set by services/consolidation.py::mark_in_transit) -
    deliberately not a second table: this system only ever has one
    international shipment leg per consolidation batch, so splitting them
    would just be the same row normalized across two tables for no
    behavioral benefit. See docs/VNKE_ROADMAP.md Phase 6 for the reasoning."""

    __tablename__ = "consolidations"

    consolidation_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    # Set once the batch departs and becomes a real international shipment
    # leg (services/consolidation.py::mark_in_transit) - null before then.
    shipment_code: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)
    origin_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    destination_warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True
    )
    freight_method: Mapped[str | None] = mapped_column(String, nullable=True)
    freight_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    carrier: Mapped[str | None] = mapped_column(String, nullable=True)
    carrier_tracking_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    current_location: Mapped[str | None] = mapped_column(String, nullable=True)
    total_weight_grams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_volume_cbm: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    declared_value_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    departure_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ConsolidationStatus] = mapped_column(
        Enum(ConsolidationStatus, name="consolidation_status"), default=ConsolidationStatus.OPEN, nullable=False
    )

    origin_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[origin_warehouse_id])
    destination_warehouse: Mapped["Warehouse | None"] = relationship(foreign_keys=[destination_warehouse_id])
    packages: Mapped[list["Package"]] = relationship(back_populates="consolidation")
