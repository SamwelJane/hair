import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import PaymentProviderType, PaymentStatus


class AdminPaymentListItemOut(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_email: str
    provider: PaymentProviderType
    status: PaymentStatus
    amount_kes: Decimal
    provider_ref: str | None
    confirmed_by_name: str | None
    created_at: datetime


class AdminPaymentsOut(BaseModel):
    pending_bank_transfers: list[AdminPaymentListItemOut]
    mpesa_payments: list[AdminPaymentListItemOut]
    resolved_bank_transfers: list[AdminPaymentListItemOut]
