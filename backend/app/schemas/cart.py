import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(ge=1, le=50)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1, le=50)


class MergeGuestCartRequest(BaseModel):
    guest_token: str


class CartItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: int
    unit_price_usd: Decimal
    name: str
    slug: str
    image_url: str | None = None
    variant_label: str | None = None


class CartOut(BaseModel):
    id: uuid.UUID
    guest_token: str | None
    items: list[CartItemOut]
