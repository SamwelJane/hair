import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    AttachmentType,
    DrawnType,
    HairCategory,
    TextureCategory,
    TipType,
    WigConstruction,
)


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
    image_url: str | None = None


class SupplierPublicOut(BaseModel):
    """Public storefront view of a Supplier - deliberately narrower than
    admin_suppliers.SupplierOut, which also exposes email/whatsapp_number/
    default_margin_pct (internal business terms, not for public display)."""

    id: uuid.UUID
    name: str
    country: str


class ProductListItemOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    base_price_usd: Decimal
    country_of_origin: str
    hair_category: HairCategory
    image_url: str | None
    average_rating: float | None
    review_count: int


class ProductListOut(BaseModel):
    items: list[ProductListItemOut]
    total: int
    page: int
    page_size: int


class ProductVariantPublicOut(BaseModel):
    id: uuid.UUID
    sku: str
    length: str | None
    length_inches: int | None
    density: str | None
    texture: str | None
    color: str | None
    price_delta_usd: Decimal
    stock_qty: int
    weight_override_grams: int | None


class ProductImagePublicOut(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID | None
    url: str
    alt_text: str | None
    sort_order: int


class ReviewPublicOut(BaseModel):
    id: uuid.UUID
    rating: int
    body: str
    user_name: str
    created_at: datetime


class ProductDetailOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    category: CategoryOut
    supplier: SupplierPublicOut
    country_of_origin: str
    base_price_usd: Decimal
    hair_category: HairCategory
    hair_length: str | None
    texture: str | None
    color: str | None
    quality: str | None
    accessory_type: str | None
    processing_time_days: int
    base_weight_grams: int
    drawn_type: DrawnType | None
    texture_category: TextureCategory | None
    attachment_type: AttachmentType | None
    tip_type: TipType | None
    wig_construction: WigConstruction | None
    wig_cap_size: str | None
    wig_features: list[str]
    variants: list[ProductVariantPublicOut] = Field(default_factory=list)
    images: list[ProductImagePublicOut] = Field(default_factory=list)
    reviews: list[ReviewPublicOut] = Field(default_factory=list)
    average_rating: float | None
    # Populated when an active HomepageProductPlacement(section=DEAL) exists
    # for this product - see services/homepage.py::get_active_deal_for_product.
    sale_price_usd: Decimal | None = None
    deal_ends_at: datetime | None = None


class VariantFacetsOut(BaseModel):
    lengths: list[str]
    textures: list[str]
    colors: list[str]
