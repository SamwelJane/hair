import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product, ProductVariant
from app.models.pricing import CountryShippingRule, DiscountCode
from app.services.pricing_engine import (
    CalculatePriceInput,
    DiscountCodeInput,
    PriceBreakdown,
    PriceLineItem,
    ShippingRuleInput,
    calculate_price,
)
from app.services.pricing_settings import find_active_discount_code, get_pricing_settings


class ShippingRuleNotFoundError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


@dataclass
class CartLineInput:
    product_id: uuid.UUID
    quantity: int
    variant_id: uuid.UUID | None = None


@dataclass
class ResolvedCartLine:
    product_id: uuid.UUID
    quantity: int
    unit_price_usd: Decimal
    weight_grams: int
    margin_pct: Decimal
    variant_id: uuid.UUID | None = None


@dataclass
class CartBreakdownResult:
    breakdown: PriceBreakdown
    resolved_lines: list[ResolvedCartLine]
    applied_discount: DiscountCode | None


async def resolve_cart_lines(
    db: AsyncSession, items: list[CartLineInput], default_margin_pct: Decimal
) -> list[ResolvedCartLine]:
    """`default_margin_pct` is the platform-wide fallback (PricingSetting.
    commission_pct) used when a supplier's own default_margin_pct is still at
    its unset default (0) - there's no separate "has this supplier customized
    their margin?" flag on the schema, so 0 is treated as "not customized
    yet", matching the old app's `|| defaultMarginPct` fallback."""
    resolved: list[ResolvedCartLine] = []

    for item in items:
        product = await db.get(
            Product, item.product_id, options=[selectinload(Product.supplier)]
        )
        if product is None:
            raise ProductNotFoundError(f"Product {item.product_id} not found")

        variant: ProductVariant | None = None
        if item.variant_id is not None:
            variant = await db.get(ProductVariant, item.variant_id)

        unit_price_usd = product.base_price_usd + (variant.price_delta_usd if variant else Decimal(0))
        weight_per_unit = variant.weight_override_grams if variant and variant.weight_override_grams else product.base_weight_grams
        margin_pct = product.supplier.default_margin_pct or default_margin_pct

        resolved.append(
            ResolvedCartLine(
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price_usd=Decimal(unit_price_usd),
                weight_grams=weight_per_unit * item.quantity,
                margin_pct=Decimal(margin_pct),
            )
        )

    return resolved


async def calculate_cart_breakdown(
    db: AsyncSession,
    items: list[CartLineInput],
    country_code: str,
    discount_code: str | None = None,
) -> CartBreakdownResult:
    settings = await get_pricing_settings(db)

    shipping_rule = await db.scalar(
        select(CountryShippingRule).where(CountryShippingRule.country_code == country_code)
    )
    if shipping_rule is None:
        raise ShippingRuleNotFoundError(f"No shipping rule configured for country {country_code}")

    discount = await find_active_discount_code(db, discount_code) if discount_code else None
    resolved_lines = await resolve_cart_lines(db, items, Decimal(settings.commission_pct))

    breakdown = calculate_price(
        CalculatePriceInput(
            items=[
                PriceLineItem(unit_price_usd=line.unit_price_usd, quantity=line.quantity, margin_pct=line.margin_pct)
                for line in resolved_lines
            ],
            total_weight_grams=sum(line.weight_grams for line in resolved_lines),
            shipping_rule=ShippingRuleInput(
                base_fee_usd=Decimal(shipping_rule.base_fee_usd),
                per_kg_fee_usd=Decimal(shipping_rule.per_kg_fee_usd),
                customs_rate_pct=Decimal(shipping_rule.customs_rate_pct),
            ),
            shipping_per_kg_usd=Decimal(settings.shipping_per_kg_usd),
            packaging_fee_usd=Decimal(settings.packaging_fee_usd),
            commission_pct=Decimal(settings.commission_pct),
            discount_code=(
                DiscountCodeInput(
                    type=discount.type,
                    value=Decimal(discount.value),
                    min_order_usd=Decimal(discount.min_order_usd) if discount.min_order_usd is not None else None,
                )
                if discount is not None
                else None
            ),
        )
    )

    return CartBreakdownResult(breakdown=breakdown, resolved_lines=resolved_lines, applied_discount=discount)
