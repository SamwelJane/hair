import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import DiscountType

if TYPE_CHECKING:
    from app.models.identity import User


class DiscountCode(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "discount_codes"

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    type: Mapped[DiscountType] = mapped_column(Enum(DiscountType, name="discount_type"), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Renamed from the old app's `active` at the API/schema layer to
    # `is_enabled`: the raw on/off switch alone doesn't mean "currently
    # usable" (expiry/usage-limit also matter) - see schemas.pricing.DiscountCodeStatus
    # for the computed ACTIVE|EXPIRED|EXHAUSTED|DISABLED status.
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CountryShippingRule(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "country_shipping_rules"

    country_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    country_name: Mapped[str] = mapped_column(String, nullable=False)
    base_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    per_kg_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    customs_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    estimated_days_min: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_days_max: Mapped[int] = mapped_column(Integer, nullable=False)


class PricingSetting(Base, UpdatedAtMixin):
    """Singleton row (id='global'). Admin-configurable checkout math inputs."""

    __tablename__ = "pricing_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default="global")
    commission_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10, nullable=False)
    shipping_per_kg_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=60, nullable=False)
    packaging_fee_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=2, nullable=False)
    kes_adjustment: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=4, nullable=False)


class ExchangeRate(Base, UUIDPrimaryKeyMixin, UpdatedAtMixin):
    """Admin-set manual USD -> KES conversion rate. No live FX API, by design -
    history of who changed it and when is captured via AuditLog."""

    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("base_currency", "target_currency"),)

    base_currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    target_currency: Mapped[str] = mapped_column(String, default="KES", nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    updated_by: Mapped["User"] = relationship("User")
