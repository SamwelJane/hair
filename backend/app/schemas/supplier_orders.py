import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import SupplierOrderStatus


class SupplierOrderItemOut(BaseModel):
    product_name: str
    variant_sku: str | None
    quantity: int


class SupplierOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    sub_order_number: str | None
    customer_name: str
    status: SupplierOrderStatus
    sent_at: datetime
    eta_days: int | None
    decline_reason: str | None
    items: list[SupplierOrderItemOut]


class UpdateSupplierOrderStatusRequest(BaseModel):
    to_status: SupplierOrderStatus
    eta_days: int | None = Field(default=None, ge=0)
    decline_reason: str | None = Field(default=None, min_length=1)
