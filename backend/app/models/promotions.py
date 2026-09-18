import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import PromotionSlot, PromotionStatus

if TYPE_CHECKING:
    from app.models.catalog import Product, Supplier
    from app.models.identity import User


class SupplierPromotionRequest(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    """Allows suppliers to request promotional placement on the storefront
    (hero banner, deals of the week, category top, trending badge) governed
    by an admin-approved rate card."""

    __tablename__ = "supplier_promotion_requests"

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    slot_type: Mapped[PromotionSlot] = mapped_column(
        Enum(PromotionSlot, name="promotion_slot"), nullable=False
    )
    rate_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PromotionStatus] = mapped_column(
        Enum(PromotionStatus, name="promotion_status"), default=PromotionStatus.PENDING, nullable=False
    )
    banner_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    custom_headline: Mapped[str | None] = mapped_column(String, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Performance metrics
    impressions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    supplier: Mapped["Supplier"] = relationship()
    product: Mapped["Product"] = relationship()
    reviewed_by: Mapped["User | None"] = relationship()
