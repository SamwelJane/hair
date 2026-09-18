import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import OrderStatus
from app.schemas.pricing import CartItemIn


class ShippingAddressIn(BaseModel):
    full_name: str = Field(min_length=1)
    # Required for guest checkout (no session) to identify/create the order's
    # owner; logged-in checkout ignores this and uses the session's user id.
    email: EmailStr | None = None
    line1: str = Field(min_length=1)
    line2: str | None = None
    city: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    postal_code: str | None = None
    phone: str = Field(min_length=7)


class CheckoutRequest(BaseModel):
    items: list[CartItemIn] = Field(min_length=1)
    shipping_address: ShippingAddressIn
    discount_code: str | None = None
    payment_method: Literal["MPESA", "BANK_TRANSFER"]
    mpesa_phone: str | None = None


class CheckoutResponse(BaseModel):
    order_number: str
    tracking_number: str
    payment_instructions: dict[str, Any]
    guest_access_token: str | None = None


class OrderItemOut(BaseModel):
    product_id: uuid.UUID
    product_name: str
    product_slug: str
    variant_id: uuid.UUID | None
    variant_label: str | None
    quantity: int
    unit_price_usd_at_purchase: Decimal
    line_total_usd: Decimal


class OrderListItemOut(BaseModel):
    order_number: str
    tracking_number: str
    status: OrderStatus
    currency: str
    total_amount_usd: Decimal
    total_amount_kes: Decimal | None
    created_at: datetime


class OrderListOut(BaseModel):
    orders: list[OrderListItemOut]
    total: int
    page: int
    page_size: int


class OrderPackageOut(BaseModel):
    # Deliberately thin compared to the admin/warehouse package view - no
    # consolidation/shipment codes, since the customer "should not need to
    # understand consolidation, freight forwarding, or warehouse processing"
    # (spec section 22). Just enough for the multi-package breakdown spec
    # section 56 asks for on the customer's own order page.
    package_code: str
    status: str


class OrderOut(BaseModel):
    id: uuid.UUID
    order_number: str
    tracking_number: str
    status: OrderStatus
    currency: str
    subtotal_usd: Decimal
    shipping_fee_usd: Decimal
    handling_fee_usd: Decimal
    customs_estimate_usd: Decimal
    total_amount_usd: Decimal
    total_amount_kes: Decimal | None
    shipping_country: str
    shipping_address: dict[str, Any]
    items: list[OrderItemOut]
    packages: list[OrderPackageOut]
