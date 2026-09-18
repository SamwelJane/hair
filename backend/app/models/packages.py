import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import PackageCondition, PackageQCStatus, PackageStatus

if TYPE_CHECKING:
    from app.models.consolidation import Consolidation
    from app.models.external_shipments import ExternalShipment
    from app.models.identity import User
    from app.models.orders import Order
    from app.models.payments import SupplierOrder
    from app.models.warehouse import Warehouse


class Package(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """A physical parcel. Exactly one of order_id/external_shipment_id is set
    (enforced by the CHECK constraint below) - a platform order's package is
    created against the order that already has a tracking number, an
    external shipment's package is created against the intake record that
    generated its own. supplier_order_id is set when the order spans
    multiple suppliers, so each supplier's portion can be tracked as its own
    package(s) (see SupplierOrder)."""

    __tablename__ = "packages"
    __table_args__ = (
        CheckConstraint(
            "(order_id IS NOT NULL AND external_shipment_id IS NULL) "
            "OR (order_id IS NULL AND external_shipment_id IS NOT NULL)",
            name="ck_packages_exactly_one_owner",
        ),
    )

    package_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    external_shipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_shipments.id"), nullable=True
    )
    supplier_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_orders.id"), nullable=True
    )
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    consolidation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consolidations.id"), nullable=True
    )

    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    length_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    width_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    volume_cbm: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    qc_status: Mapped[PackageQCStatus] = mapped_column(
        Enum(PackageQCStatus, name="package_qc_status"), default=PackageQCStatus.PENDING, nullable=False
    )
    condition: Mapped[PackageCondition | None] = mapped_column(
        Enum(PackageCondition, name="package_condition"), nullable=True
    )
    photo_urls: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    location_code: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus, name="package_status"), default=PackageStatus.EXPECTED, nullable=False
    )

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    label_printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    label_reprint_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    order: Mapped["Order | None"] = relationship(back_populates="packages")
    external_shipment: Mapped["ExternalShipment | None"] = relationship(back_populates="packages")
    supplier_order: Mapped["SupplierOrder | None"] = relationship()
    warehouse: Mapped["Warehouse | None"] = relationship()
    consolidation: Mapped["Consolidation | None"] = relationship(back_populates="packages")
    received_by: Mapped["User | None"] = relationship()
