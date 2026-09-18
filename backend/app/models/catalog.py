import uuid
from decimal import Decimal

from sqlalchemy import ARRAY, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AttachmentType,
    DrawnType,
    HairCategory,
    ProductStatus,
    TextureCategory,
    TipType,
    WigConstruction,
)


class Category(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    # Homepage "Shop by Category" tile support - image/cloudinary_public_id
    # follow the same pattern as ProductImage below (public_id kept so
    # cloudinary.destroy() can clean up the asset on replace/delete).
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    cloudinary_public_id: Mapped[str | None] = mapped_column(String, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")


class Supplier(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "suppliers"

    # New vs. the old app: suppliers were matched to a login only by comparing
    # lowercased email strings (no FK). user_id is a real, resolvable link -
    # ownership checks in the supplier portal filter on this, not on email.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    whatsapp_number: Mapped[str] = mapped_column(String, nullable=False)
    default_margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)  # active | inactive


class Product(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hair_length: Mapped[str | None] = mapped_column(String, nullable=True)
    texture: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    quality: Mapped[str | None] = mapped_column(String, nullable=True)
    accessory_type: Mapped[str | None] = mapped_column(String, nullable=True)
    country_of_origin: Mapped[str] = mapped_column(String, nullable=False)
    processing_time_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    base_price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_weight_grams: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status"), default=ProductStatus.DRAFT, nullable=False
    )

    # Hair taxonomy, from the supplier catalogue's own classification:
    # Product -> Quality (drawn_type) -> Length -> Texture -> Colour -> Attachment.
    hair_category: Mapped[HairCategory] = mapped_column(
        Enum(HairCategory, name="hair_category"), default=HairCategory.BULK_HAIR, nullable=False
    )
    drawn_type: Mapped[DrawnType | None] = mapped_column(Enum(DrawnType, name="drawn_type"), nullable=True)
    texture_category: Mapped[TextureCategory | None] = mapped_column(
        Enum(TextureCategory, name="texture_category"), nullable=True
    )
    attachment_type: Mapped[AttachmentType | None] = mapped_column(
        Enum(AttachmentType, name="attachment_type"), nullable=True
    )
    tip_type: Mapped[TipType | None] = mapped_column(Enum(TipType, name="tip_type"), nullable=True)
    wig_construction: Mapped[WigConstruction | None] = mapped_column(
        Enum(WigConstruction, name="wig_construction"), nullable=True
    )
    wig_cap_size: Mapped[str | None] = mapped_column(String, nullable=True)
    wig_features: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    category: Mapped[Category] = relationship()
    supplier: Mapped[Supplier] = relationship()
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    length: Mapped[str | None] = mapped_column(String, nullable=True)
    length_inches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    density: Mapped[str | None] = mapped_column(String, nullable=True)
    texture: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    sku: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price_delta_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weight_override_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)

    product: Mapped[Product] = relationship(back_populates="variants")


# Reference/lookup data only (no FK from Product/ProductVariant) - these exist
# to drive clean dropdowns matching the catalogue's exact values. Kept
# unlinked deliberately: taxonomy values are supplier-driven free text, and
# forcing an FK would block product creation for any value not yet
# catalogued. Product/ProductVariant color and length columns stay plain
# strings, populated from the picked row's display name.
class HairColor(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "hair_colors"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hex_swatch: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class HairLength(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "hair_lengths"

    inches: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    cm: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProductImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    # New vs. the old app: only `url` was stored there, so deleting an image
    # couldn't clean up the actual Cloudinary asset (orphaned blobs). Storing
    # the public_id makes `cloudinary.destroy()` possible at delete time.
    cloudinary_public_id: Mapped[str | None] = mapped_column(String, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped[Product] = relationship(back_populates="images")
