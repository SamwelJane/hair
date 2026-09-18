import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import HomepagePlacementSection

if TYPE_CHECKING:
    from app.models.catalog import Product


class HomepageBanner(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """A hero-carousel slide on the storefront landing page. Admin-managed -
    see routers/admin/homepage.py."""

    __tablename__ = "homepage_banners"

    # Nullable at the DB level - a banner is created first (headline/CTA),
    # then its image is set via a separate upload endpoint, mirroring the
    # create-then-upload flow ProductImage already uses. The public query
    # (services/homepage.py::get_public_homepage_content) only returns
    # banners that have an image set, so an incomplete banner never
    # accidentally appears on the live site.
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    cloudinary_public_id: Mapped[str | None] = mapped_column(String, nullable=True)
    headline: Mapped[str] = mapped_column(String, nullable=False)
    subheadline: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_label: Mapped[str | None] = mapped_column(String, nullable=True)
    cta_url: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class HomepageProductPlacement(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Puts a Product on the homepage, either as a plain 'Featured' item or a
    time-boxed 'Deal' with its own sale price - one table for both sections
    (distinguished by `section`) rather than two near-identical ones, since
    sale_price_usd/starts_at/ends_at are simply unused for FEATURED rows.
    Does not touch Product itself - a product can be featured/on deal
    without any change to its own row, and removing a placement never loses
    catalog data."""

    __tablename__ = "homepage_product_placements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    section: Mapped[HomepagePlacementSection] = mapped_column(
        Enum(HomepagePlacementSection, name="homepage_placement_section"), nullable=False
    )
    sale_price_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship()
