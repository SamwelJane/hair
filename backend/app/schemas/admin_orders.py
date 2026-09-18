import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import OrderStatus


class UpdateOrderStatusRequest(BaseModel):
    to_status: OrderStatus
    note: str | None = None


class AdminOrderListItemOut(BaseModel):
    id: uuid.UUID
    order_number: str
    tracking_number: str
    customer_email: str
    supplier_names: list[str]
    status: OrderStatus
    total_amount_usd: Decimal
    created_at: datetime


class AdminOrderListOut(BaseModel):
    orders: list[AdminOrderListItemOut]
    total: int
    page: int
    page_size: int


class OrderListFilters(BaseModel):
    q: str | None = None
    status: OrderStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
    page: int = 1


class AdminOrderItemOut(BaseModel):
    id: uuid.UUID
    product_name: str
    variant_label: str | None
    quantity: int
    line_total_usd: Decimal


class AdminOrderStatusHistoryOut(BaseModel):
    id: uuid.UUID
    to_status: OrderStatus
    changed_by_name: str | None
    note: str | None
    created_at: datetime


class AdminSupplierOrderOut(BaseModel):
    id: uuid.UUID
    supplier_name: str
    status: str


class AdminPaymentOut(BaseModel):
    id: uuid.UUID
    provider: str
    status: str
    amount_kes: Decimal
    provider_ref: str | None
    confirmed_by_name: str | None
    proof_of_payment_url: str | None


class AdminOrderPackageOut(BaseModel):
    id: uuid.UUID
    package_code: str
    status: str
    qc_status: str
    consolidation_code: str | None
    shipment_code: str | None


class AdminOrderDetailOut(BaseModel):
    id: uuid.UUID
    order_number: str
    tracking_number: str
    status: OrderStatus
    customer_name: str
    customer_email: str
    total_amount_usd: Decimal
    total_amount_kes: Decimal | None
    items: list[AdminOrderItemOut]
    supplier_orders: list[AdminSupplierOrderOut]
    payments: list[AdminPaymentOut]
    status_history: list[AdminOrderStatusHistoryOut]
    packages: list[AdminOrderPackageOut]
    next_statuses: list[OrderStatus]
