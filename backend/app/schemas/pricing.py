import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(ge=1, le=50)


class CheckoutSummaryRequest(BaseModel):
    items: list[CartItemIn] = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    discount_code: str | None = None


class PriceCalculateRequest(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(ge=1, le=50)
    country_code: str = Field(min_length=2, max_length=2)
    discount_code: str | None = None


class PriceBreakdownOut(BaseModel):
    subtotal_usd: Decimal
    shipping_fee_usd: Decimal
    handling_fee_usd: Decimal
    customs_estimate_usd: Decimal
    discount_usd: Decimal
    total_amount_usd: Decimal
    total_weight_grams: int
