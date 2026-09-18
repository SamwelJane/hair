import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    AttachmentType,
    DrawnType,
    HairCategory,
    ProductStatus,
    TextureCategory,
    TipType,
    WigConstruction,
)


class SupplierProductRequest(BaseModel):
    """Same shape as admin_products.ProductRequest minus supplier_id and
    country_of_origin - both are set server-side (from the caller's own
    Supplier record) and never trusted from the request body, mirroring the
    old app's requireSupplierWithRecord()-scoped server actions."""

    name: str = Field(min_length=1)
    category_id: uuid.UUID
    description: str = Field(min_length=1)
    base_price_usd: Decimal
    hair_category: HairCategory = HairCategory.BULK_HAIR
    hair_length: str | None = None
    texture: str | None = None
    color: str | None = None
    quality: str | None = None
    accessory_type: str | None = None
    processing_time_days: int = 7
    base_weight_grams: int = 200
    status: ProductStatus = ProductStatus.PUBLISHED
    drawn_type: DrawnType | None = None
    texture_category: TextureCategory | None = None
    attachment_type: AttachmentType | None = None
    tip_type: TipType | None = None
    wig_construction: WigConstruction | None = None
    wig_cap_size: str | None = None
    wig_features: list[str] = Field(default_factory=list)


class SupplierVariantRequest(BaseModel):
    sku: str = Field(min_length=1)
    length: str | None = None
    density: str | None = None
    texture: str | None = None
    color: str | None = None
    price_delta_usd: Decimal = Decimal(0)
    stock_qty: int = 0
    weight_override_grams: int | None = None


class SupplierProductVariantOut(BaseModel):
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


class SupplierProductImageOut(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID | None
    url: str
    alt_text: str | None
    sort_order: int


class SupplierProductOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category_id: uuid.UUID
    description: str
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
    status: ProductStatus
    drawn_type: DrawnType | None
    texture_category: TextureCategory | None
    attachment_type: AttachmentType | None
    tip_type: TipType | None
    wig_construction: WigConstruction | None
    wig_cap_size: str | None
    wig_features: list[str]
    variants: list[SupplierProductVariantOut] = Field(default_factory=list)
    images: list[SupplierProductImageOut] = Field(default_factory=list)
