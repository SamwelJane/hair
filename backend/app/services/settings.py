import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import CountryShippingRule, DiscountCode, ExchangeRate, PricingSetting
from app.services.audit import log_audit
from app.services.pricing_settings import get_pricing_settings


class DiscountCodeNotFoundError(Exception):
    pass


class ShippingRuleNotFoundError(Exception):
    pass


async def create_discount_code(
    db: AsyncSession,
    *,
    code: str,
    discount_type: str,
    value: Decimal,
    min_order_usd: Decimal | None,
    usage_limit: int | None,
    expires_at: date | None,
    actor_user_id: uuid.UUID,
) -> DiscountCode:
    normalized_code = code.strip().upper()
    discount = DiscountCode(
        code=normalized_code,
        type=discount_type,
        value=value,
        min_order_usd=min_order_usd,
        usage_limit=usage_limit,
        expires_at=datetime.combine(expires_at, datetime.min.time()).replace(tzinfo=UTC) if expires_at else None,
    )
    db.add(discount)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_DISCOUNT_CODE", entity_type="DiscountCode",
        entity_id=normalized_code,
        metadata={
            "type": discount_type, "value": str(value),
            "minOrderUsd": str(min_order_usd) if min_order_usd else None,
        },
    )
    await db.commit()
    await db.refresh(discount)
    return discount


async def toggle_discount_code_active(db: AsyncSession, discount_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> DiscountCode:
    discount = await db.get(DiscountCode, discount_id)
    if discount is None:
        raise DiscountCodeNotFoundError(f"Discount code {discount_id} not found")

    discount.active = not discount.active
    await log_audit(
        db, user_id=actor_user_id,
        action="ACTIVATE_DISCOUNT_CODE" if discount.active else "DEACTIVATE_DISCOUNT_CODE",
        entity_type="DiscountCode", entity_id=str(discount_id),
    )
    await db.commit()
    await db.refresh(discount)
    return discount


async def update_exchange_rate(db: AsyncSession, *, rate: Decimal, actor_user_id: uuid.UUID) -> ExchangeRate:
    existing = await db.scalar(
        select(ExchangeRate).where(ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == "KES")
    )
    previous_rate = existing.rate if existing else None

    if existing is not None:
        existing.rate = rate
        existing.updated_by_id = actor_user_id
        record = existing
    else:
        record = ExchangeRate(base_currency="USD", target_currency="KES", rate=rate, updated_by_id=actor_user_id)
        db.add(record)

    await log_audit(
        db, user_id=actor_user_id, action="UPDATE_EXCHANGE_RATE", entity_type="ExchangeRate", entity_id="USD_KES",
        metadata={"from": str(previous_rate) if previous_rate is not None else None, "to": str(rate)},
    )
    await db.commit()
    await db.refresh(record)
    return record


async def update_pricing_settings(
    db: AsyncSession,
    *,
    commission_pct: Decimal,
    shipping_per_kg_usd: Decimal,
    packaging_fee_usd: Decimal,
    kes_adjustment: Decimal,
    actor_user_id: uuid.UUID,
) -> PricingSetting:
    settings = await get_pricing_settings(db)
    settings.commission_pct = commission_pct
    settings.shipping_per_kg_usd = shipping_per_kg_usd
    settings.packaging_fee_usd = packaging_fee_usd
    settings.kes_adjustment = kes_adjustment

    await log_audit(
        db, user_id=actor_user_id, action="UPDATE_PRICING_SETTINGS", entity_type="PricingSetting",
        entity_id="global",
        metadata={
            "commissionPct": str(commission_pct), "shippingPerKgUsd": str(shipping_per_kg_usd),
            "packagingFeeUsd": str(packaging_fee_usd), "kesAdjustment": str(kes_adjustment),
        },
    )
    await db.commit()
    await db.refresh(settings)
    return settings


async def upsert_shipping_rule(
    db: AsyncSession,
    *,
    country_code: str,
    country_name: str,
    base_fee_usd: Decimal,
    per_kg_fee_usd: Decimal,
    customs_rate_pct: Decimal,
    estimated_days_min: int,
    estimated_days_max: int,
    actor_user_id: uuid.UUID,
) -> CountryShippingRule:
    normalized_code = country_code.strip().upper()
    existing = await db.scalar(select(CountryShippingRule).where(CountryShippingRule.country_code == normalized_code))

    if existing is not None:
        existing.country_name = country_name
        existing.base_fee_usd = base_fee_usd
        existing.per_kg_fee_usd = per_kg_fee_usd
        existing.customs_rate_pct = customs_rate_pct
        existing.estimated_days_min = estimated_days_min
        existing.estimated_days_max = estimated_days_max
        rule = existing
    else:
        rule = CountryShippingRule(
            country_code=normalized_code, country_name=country_name, base_fee_usd=base_fee_usd,
            per_kg_fee_usd=per_kg_fee_usd, customs_rate_pct=customs_rate_pct,
            estimated_days_min=estimated_days_min, estimated_days_max=estimated_days_max,
        )
        db.add(rule)

    await log_audit(
        db, user_id=actor_user_id, action="UPSERT_SHIPPING_RULE", entity_type="CountryShippingRule",
        entity_id=normalized_code, metadata={"countryName": country_name},
    )
    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_shipping_rule(db: AsyncSession, country_code: str, *, actor_user_id: uuid.UUID) -> None:
    normalized_code = country_code.strip().upper()
    rule = await db.scalar(select(CountryShippingRule).where(CountryShippingRule.country_code == normalized_code))
    if rule is None:
        raise ShippingRuleNotFoundError(f"No shipping rule for {normalized_code}")

    await db.delete(rule)
    await log_audit(
        db, user_id=actor_user_id, action="DELETE_SHIPPING_RULE", entity_type="CountryShippingRule",
        entity_id=normalized_code,
    )
    await db.commit()
