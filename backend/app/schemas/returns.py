import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ReturnStatus


class CreateReturnRequest(BaseModel):
    order_id: uuid.UUID
    reason: str = Field(min_length=1)


class MyReturnOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    reason: str
    status: ReturnStatus
    refund_amount_usd: Decimal | None
    created_at: datetime
