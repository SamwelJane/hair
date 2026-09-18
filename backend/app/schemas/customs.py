import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import CustomsStatus


class DeclareCustomsRequest(BaseModel):
    hs_code: str = Field(min_length=1)
    declared_value_usd: Decimal
    duty_usd: Decimal = Decimal(0)
    vat_usd: Decimal = Decimal(0)


class RaiseCustomsQueryRequest(BaseModel):
    note: str = Field(min_length=1)


class CustomsDeclarationOut(BaseModel):
    id: uuid.UUID
    consolidation_id: uuid.UUID | None
    package_id: uuid.UUID | None
    consolidation_code: str | None
    hs_code: str | None
    declared_value_usd: Decimal | None
    duty_usd: Decimal
    vat_usd: Decimal
    status: CustomsStatus
    notes: str | None
    created_at: datetime


class CustomsDeclarationListOut(BaseModel):
    declarations: list[CustomsDeclarationOut]
    total: int
    page: int
    page_size: int
