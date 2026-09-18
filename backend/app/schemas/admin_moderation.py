import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.models.enums import ReturnStatus, ReviewStatus


class ResolveReturnRequest(BaseModel):
    status: Literal[ReturnStatus.APPROVED, ReturnStatus.REJECTED, ReturnStatus.REFUNDED]
    refund_amount_usd: Decimal | None = None


class ReturnOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    customer_email: str
    reason: str
    status: ReturnStatus
    refund_amount_usd: Decimal | None
    resolved_by_name: str | None
    created_at: datetime


class ModerateReviewRequest(BaseModel):
    status: Literal[ReviewStatus.APPROVED, ReviewStatus.REJECTED]


class ReviewOut(BaseModel):
    id: uuid.UUID
    product_name: str
    user_name: str
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime
