import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    AttachmentType,
    DrawnType,
    HairCategory,
    HomepagePlacementSection,
    ProductStatus,
    TextureCategory,
    TipType,
    WigConstruction,
)


class ProductRequest(BaseModel):
    name: str = Field(min_length=1)
    category_id: uuid.UUID
    supplier_id: uuid.UUID
    description: str = Field(min_length=1)
    country_of_origin: str = Field(min_length=1)
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


class VariantRequest(BaseModel):
    sku: str = Field(min_length=1)
    length: str | None = None
    density: str | None = None
    texture: str | None = None
    color: str | None = None
    price_delta_usd: Decimal = Decimal(0)
    stock_qty: int = 0
    weight_override_grams: int | None = None


class ProductVariantOut(BaseModel):
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


class ProductImageOut(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID | None
    url: str
    alt_text: str | None
    sort_order: int


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category_id: uuid.UUID
    supplier_id: uuid.UUID
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
    variants: list[ProductVariantOut] = Field(default_factory=list)
    images: list[ProductImageOut] = Field(default_factory=list)


class AdminProductListItemOut(BaseModel):
    id: uuid.UUID
    name: str
    category_name: str
    supplier_name: str
    base_price_usd: Decimal
    variant_count: int
    status: ProductStatus


class AdminProductListOut(BaseModel):
    items: list[AdminProductListItemOut]
    total: int
    page: int
    page_size: int


class CategoryRequest(BaseModel):
    name: str = Field(min_length=1)


class CategoryUpdateRequest(BaseModel):
    name: str = Field(min_length=1)
    is_featured: bool = False
    sort_order: int = 0


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
    image_url: str | None = None
    is_featured: bool = False
    sort_order: int = 0


class BannerRequest(BaseModel):
    headline: str = Field(min_length=1)
    subheadline: str | None = None
    cta_label: str | None = None
    cta_url: str | None = None
    sort_order: int = 0
    is_active: bool = True


class BannerOut(BaseModel):
    id: uuid.UUID
    image_url: str | None
    headline: str
    subheadline: str | None
    cta_label: str | None
    cta_url: str | None
    sort_order: int
    is_active: bool


class ProductPlacementRequest(BaseModel):
    product_id: uuid.UUID
    section: HomepagePlacementSection
    sale_price_usd: Decimal | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    sort_order: int = 0
    is_active: bool = True


class ProductPlacementUpdateRequest(BaseModel):
    # No product_id - which product a placement points to isn't editable,
    # only its section/pricing/scheduling/visibility. Delete and recreate to
    # point a placement at a different product.
    section: HomepagePlacementSection
    sale_price_usd: Decimal | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    sort_order: int = 0
    is_active: bool = True


class ProductPlacementOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_slug: str
    section: HomepagePlacementSection
    sale_price_usd: Decimal | None
    starts_at: datetime | None
    ends_at: datetime | None
    sort_order: int
    is_active: bool
