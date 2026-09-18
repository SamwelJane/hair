import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReviewStatus


class CreateReviewRequest(BaseModel):
    order_id: uuid.UUID
    product_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=1)


class MyReviewOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    order_id: uuid.UUID | None
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime
