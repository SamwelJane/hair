import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import OrderStatus, ReturnStatus, ReviewStatus

if TYPE_CHECKING:
    from app.models.catalog import Product, ProductVariant
    from app.models.identity import User
    from app.models.packages import Package
    from app.models.payments import Payment, SupplierOrder


class Order(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    # Immutable once set - generated at order-creation time (routers/orders.py
    # ::checkout) and never regenerated, including by warehouse
    # receiving/labeling/reprinting later in the fulfilment lifecycle.
    tracking_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.PENDING_PAYMENT, nullable=False
    )
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    subtotal_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    handling_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    packaging_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=2, nullable=False)
    customs_estimate_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    subtotal_supplier_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    platform_margin_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cancellation_fee_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    refund_amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discount_codes.id"), nullable=True
    )
    total_amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    exchange_rate_applied: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    total_amount_kes: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_country: Mapped[str] = mapped_column(String(2), nullable=False)
    shipping_address: Mapped[dict] = mapped_column(JSONB, nullable=False)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    supplier_orders: Mapped[list["SupplierOrder"]] = relationship(back_populates="order")
    packages: Mapped[list["Package"]] = relationship(back_populates="order")


class Return(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "returns"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus, name="return_status"), default=ReturnStatus.REQUESTED, nullable=False
    )
    refund_amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship()
    requested_by: Mapped["User"] = relationship(foreign_keys=[requested_by_id])
    resolved_by: Mapped["User | None"] = relationship(foreign_keys=[resolved_by_id])


class OrderItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_usd_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant | None"] = relationship()


class OrderStatusHistory(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[OrderStatus | None] = mapped_column(Enum(OrderStatus, name="order_status"), nullable=True)
    to_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship()


class Review(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "reviews"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"), default=ReviewStatus.PENDING, nullable=False
    )

    product: Mapped["Product"] = relationship()
    user: Mapped["User"] = relationship()
