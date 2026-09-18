import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class CreateSupplierRequest(BaseModel):
    name: str = Field(min_length=1)
    country: str = Field(min_length=1)
    email: EmailStr
    whatsapp_number: str = Field(min_length=1)
    default_margin_pct: Decimal = Decimal(0)
    temporary_password: str | None = Field(default=None, min_length=8)


class SupplierOut(BaseModel):
    id: uuid.UUID
    name: str
    country: str
    email: str
    whatsapp_number: str
    default_margin_pct: Decimal
    status: str
    user_id: uuid.UUID | None
    product_count: int = 0


class SupplierPerformanceOut(BaseModel):
    total_orders: int
    completed_orders: int
    avg_processing_days: float | None
    on_time_rate_pct: float | None


class PendingSupplierOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    customer_email: str
    status: str
    sent_at: datetime


class SupplierDetailOut(BaseModel):
    supplier: SupplierOut
    performance: SupplierPerformanceOut
    pending_orders: list[PendingSupplierOrderOut]
