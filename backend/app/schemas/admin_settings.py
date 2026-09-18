import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CreateDiscountCodeRequest(BaseModel):
    code: str = Field(min_length=1)
    type: Literal["percent", "fixed"]
    value: Decimal
    min_order_usd: Decimal | None = None
    usage_limit: int | None = None
    expires_at: date | None = None


class DiscountCodeOut(BaseModel):
    id: uuid.UUID
    code: str
    type: str
    value: Decimal
    min_order_usd: Decimal | None
    usage_limit: int | None
    times_used: int
    expires_at: datetime | None
    is_enabled: bool
    status: Literal["ACTIVE", "EXPIRED", "EXHAUSTED", "DISABLED"]


class UpdateExchangeRateRequest(BaseModel):
    rate: Decimal = Field(gt=0)


class ExchangeRateOut(BaseModel):
    rate: Decimal
    updated_by_name: str
    updated_at: datetime


class UpdatePricingSettingsRequest(BaseModel):
    commission_pct: Decimal = Field(ge=0)
    shipping_per_kg_usd: Decimal = Field(ge=0)
    packaging_fee_usd: Decimal = Field(ge=0)
    kes_adjustment: Decimal


class PricingSettingsOut(BaseModel):
    commission_pct: Decimal
    shipping_per_kg_usd: Decimal
    packaging_fee_usd: Decimal
    kes_adjustment: Decimal


class UpsertShippingRuleRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str = Field(min_length=1)
    base_fee_usd: Decimal
    per_kg_fee_usd: Decimal
    customs_rate_pct: Decimal = Decimal(0)
    estimated_days_min: int
    estimated_days_max: int


class ShippingRuleOut(BaseModel):
    country_code: str
    country_name: str
    base_fee_usd: Decimal
    per_kg_fee_usd: Decimal
    customs_rate_pct: Decimal
    estimated_days_min: int
    estimated_days_max: int
