import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentProviderType, PaymentStatus, SupplierOrderStatus

if TYPE_CHECKING:
    from app.models.catalog import Supplier
    from app.models.identity import User
    from app.models.orders import Order


class Payment(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[PaymentProviderType] = mapped_column(
        Enum(PaymentProviderType, name="payment_provider_type"), nullable=False
    )
    provider_ref: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    amount_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.INITIATED, nullable=False
    )
    raw_callback_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proof_of_payment_url: Mapped[str | None] = mapped_column(String, nullable=True)
    confirmed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="payments")
    confirmed_by: Mapped["User | None"] = relationship()


class SupplierOrder(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "supplier_orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[SupplierOrderStatus] = mapped_column(
        Enum(SupplierOrderStatus, name="supplier_order_status"), default=SupplierOrderStatus.SENT, nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    eta_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="supplier_orders")
    supplier: Mapped["Supplier"] = relationship()
