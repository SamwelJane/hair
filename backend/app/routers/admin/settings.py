import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin, require_strict_admin
from app.models.identity import User
from app.models.pricing import CountryShippingRule, DiscountCode, ExchangeRate
from app.schemas.admin_settings import (
    CreateDiscountCodeRequest,
    DiscountCodeOut,
    ExchangeRateOut,
    PricingSettingsOut,
    ShippingRuleOut,
    UpdateExchangeRateRequest,
    UpdatePricingSettingsRequest,
    UpsertShippingRuleRequest,
)
from app.services import settings as settings_service
from app.services.pricing_settings import get_pricing_settings

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"], dependencies=[Depends(require_admin)])


def _discount_status(discount: DiscountCode) -> Literal["ACTIVE", "EXPIRED", "EXHAUSTED", "DISABLED"]:
    if not discount.active:
        return "DISABLED"
    if discount.expires_at is not None and discount.expires_at < datetime.now(UTC):
        return "EXPIRED"
    if discount.usage_limit is not None and discount.times_used >= discount.usage_limit:
        return "EXHAUSTED"
    return "ACTIVE"


def _discount_to_out(discount: DiscountCode) -> DiscountCodeOut:
    return DiscountCodeOut(
        id=discount.id, code=discount.code, type=discount.type, value=discount.value,
        min_order_usd=discount.min_order_usd, usage_limit=discount.usage_limit, times_used=discount.times_used,
        expires_at=discount.expires_at, is_enabled=discount.active, status=_discount_status(discount),
    )


# ---------- Discount codes (STRICT admin) ----------


@router.get("/discount-codes", response_model=list[DiscountCodeOut])
async def list_discount_codes(db: AsyncSession = Depends(get_db)) -> list[DiscountCodeOut]:
    codes = (await db.execute(select(DiscountCode).order_by(DiscountCode.created_at.desc()))).scalars().all()
    return [_discount_to_out(c) for c in codes]


@router.post("/discount-codes", response_model=DiscountCodeOut, status_code=201)
async def create_discount_code(
    payload: CreateDiscountCodeRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> DiscountCodeOut:
    discount = await settings_service.create_discount_code(
        db, code=payload.code, discount_type=payload.type, value=payload.value, min_order_usd=payload.min_order_usd,
        usage_limit=payload.usage_limit, expires_at=payload.expires_at, actor_user_id=admin.id,
    )
    return _discount_to_out(discount)


@router.post("/discount-codes/{discount_id}/toggle-active", response_model=DiscountCodeOut)
async def toggle_discount_code(
    discount_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> DiscountCodeOut:
    try:
        discount = await settings_service.toggle_discount_code_active(db, discount_id, actor_user_id=admin.id)
    except settings_service.DiscountCodeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _discount_to_out(discount)


# ---------- Exchange rate (STRICT admin) ----------


@router.get("/exchange-rate", response_model=ExchangeRateOut | None)
async def get_exchange_rate(db: AsyncSession = Depends(get_db)) -> ExchangeRateOut | None:
    rate = await db.scalar(
        select(ExchangeRate)
        .where(ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == "KES")
        .options(selectinload(ExchangeRate.updated_by))
    )
    if rate is None:
        return None
    return ExchangeRateOut(rate=rate.rate, updated_by_name=rate.updated_by.name, updated_at=rate.updated_at)


@router.put("/exchange-rate", response_model=ExchangeRateOut)
async def update_exchange_rate(
    payload: UpdateExchangeRateRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> ExchangeRateOut:
    rate = await settings_service.update_exchange_rate(db, rate=payload.rate, actor_user_id=admin.id)
    await db.refresh(rate, attribute_names=["updated_by"])
    return ExchangeRateOut(rate=rate.rate, updated_by_name=rate.updated_by.name, updated_at=rate.updated_at)


# ---------- Pricing settings (STRICT admin) ----------


@router.get("/pricing", response_model=PricingSettingsOut)
async def get_pricing(db: AsyncSession = Depends(get_db)) -> PricingSettingsOut:
    settings = await get_pricing_settings(db)
    return PricingSettingsOut(
        commission_pct=settings.commission_pct, shipping_per_kg_usd=settings.shipping_per_kg_usd,
        packaging_fee_usd=settings.packaging_fee_usd, kes_adjustment=settings.kes_adjustment,
    )


@router.put("/pricing", response_model=PricingSettingsOut)
async def update_pricing(
    payload: UpdatePricingSettingsRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> PricingSettingsOut:
    settings = await settings_service.update_pricing_settings(
        db, commission_pct=payload.commission_pct, shipping_per_kg_usd=payload.shipping_per_kg_usd,
        packaging_fee_usd=payload.packaging_fee_usd, kes_adjustment=payload.kes_adjustment, actor_user_id=admin.id,
    )
    return PricingSettingsOut(
        commission_pct=settings.commission_pct, shipping_per_kg_usd=settings.shipping_per_kg_usd,
        packaging_fee_usd=settings.packaging_fee_usd, kes_adjustment=settings.kes_adjustment,
    )


# ---------- Shipping rules (regular admin, NOT strict - matches the old app) ----------


@router.get("/shipping-rules", response_model=list[ShippingRuleOut])
async def list_shipping_rules(db: AsyncSession = Depends(get_db)) -> list[ShippingRuleOut]:
    rules = (
        (await db.execute(select(CountryShippingRule).order_by(CountryShippingRule.country_name))).scalars().all()
    )
    return [
        ShippingRuleOut(
            country_code=r.country_code, country_name=r.country_name, base_fee_usd=r.base_fee_usd,
            per_kg_fee_usd=r.per_kg_fee_usd, customs_rate_pct=r.customs_rate_pct,
            estimated_days_min=r.estimated_days_min, estimated_days_max=r.estimated_days_max,
        )
        for r in rules
    ]


@router.put("/shipping-rules", response_model=ShippingRuleOut)
async def upsert_shipping_rule(
    payload: UpsertShippingRuleRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> ShippingRuleOut:
    rule = await settings_service.upsert_shipping_rule(
        db, country_code=payload.country_code, country_name=payload.country_name, base_fee_usd=payload.base_fee_usd,
        per_kg_fee_usd=payload.per_kg_fee_usd, customs_rate_pct=payload.customs_rate_pct,
        estimated_days_min=payload.estimated_days_min, estimated_days_max=payload.estimated_days_max,
        actor_user_id=admin.id,
    )
    return ShippingRuleOut(
        country_code=rule.country_code, country_name=rule.country_name, base_fee_usd=rule.base_fee_usd,
        per_kg_fee_usd=rule.per_kg_fee_usd, customs_rate_pct=rule.customs_rate_pct,
        estimated_days_min=rule.estimated_days_min, estimated_days_max=rule.estimated_days_max,
    )


@router.delete("/shipping-rules/{country_code}", status_code=204)
async def delete_shipping_rule(
    country_code: str, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    try:
        await settings_service.delete_shipping_rule(db, country_code, actor_user_id=admin.id)
    except settings_service.ShippingRuleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
