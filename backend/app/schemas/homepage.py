import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BannerOut(BaseModel):
    id: uuid.UUID
    image_url: str
    headline: str
    subheadline: str | None
    cta_label: str | None
    cta_url: str | None


class CategoryTileOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    image_url: str | None


class HomepageProductOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    image_url: str | None
    base_price_usd: Decimal
    sale_price_usd: Decimal | None
    average_rating: float | None
    review_count: int
    deal_ends_at: datetime | None = None


class HomepageContentOut(BaseModel):
    banners: list[BannerOut]
    featured_categories: list[CategoryTileOut]
    featured_products: list[HomepageProductOut]
    deals: list[HomepageProductOut]
