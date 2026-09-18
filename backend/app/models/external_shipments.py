import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import ExternalShipmentStatus

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.packages import Package


class ExternalShipment(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """A shipment for a customer who bought from a Vietnamese supplier outside
    the platform (e.g. WhatsApp/Facebook). Warehouse staff create this record
    when the package arrives at Cherubim; it generates its own tracking
    number and needs no registered customer account - mirrors Cart's
    nullable-user_id/guest_token pattern for "may or may not have an
    account", but here there is never a user_id at all, only free-text
    contact details captured by staff."""

    __tablename__ = "external_shipments"

    tracking_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    customer_phone: Mapped[str] = mapped_column(String, nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String, nullable=True)
    supplier_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[ExternalShipmentStatus] = mapped_column(
        Enum(ExternalShipmentStatus, name="external_shipment_status"),
        default=ExternalShipmentStatus.ACTIVE,
        nullable=False,
    )

    created_by: Mapped["User | None"] = relationship()
    packages: Mapped[list["Package"]] = relationship(back_populates="external_shipment")
