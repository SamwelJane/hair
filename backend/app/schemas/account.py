import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import OrderStatus, PaymentProviderType, PaymentStatus, ReviewStatus, UserRole
from app.schemas.addresses import AddressOut


class AccountExportUserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    phone: str | None
    role: UserRole
    created_at: datetime


class AccountExportOrderItemOut(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: int
    unit_price_usd_at_purchase: Decimal
    line_total_usd: Decimal


class AccountExportPaymentOut(BaseModel):
    id: uuid.UUID
    provider: PaymentProviderType
    provider_ref: str | None
    amount_kes: Decimal
    status: PaymentStatus
    created_at: datetime


class AccountExportStatusHistoryOut(BaseModel):
    from_status: OrderStatus | None
    to_status: OrderStatus
    note: str | None
    created_at: datetime


class AccountExportOrderOut(BaseModel):
    order_number: str
    status: OrderStatus
    currency: str
    total_amount_usd: Decimal
    total_amount_kes: Decimal | None
    created_at: datetime
    items: list[AccountExportOrderItemOut]
    payments: list[AccountExportPaymentOut]
    status_history: list[AccountExportStatusHistoryOut]


class AccountExportReviewOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    order_id: uuid.UUID | None
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime


class AccountExportOut(BaseModel):
    user: AccountExportUserOut
    orders: list[AccountExportOrderOut]
    addresses: list[AddressOut]
    reviews: list[AccountExportReviewOut]
    exported_at: datetime
