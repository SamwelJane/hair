from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.catalog import Product, ProductVariant
from app.models.pricing import CountryShippingRule
from app.schemas.pricing import CheckoutSummaryRequest, PriceBreakdownOut, PriceCalculateRequest
from app.services import cart_breakdown as cart_breakdown_service
from app.services.pricing_engine import (
    CalculatePriceInput,
    DiscountCodeInput,
    PriceLineItem,
    ShippingRuleInput,
    calculate_price,
)
from app.services.exchange_rate import convert_usd_to_kes, get_effective_usd_to_kes_rate
from app.services.pricing_settings import find_active_discount_code, get_pricing_settings

router = APIRouter(tags=["pricing"])


def _to_breakdown_out(
    breakdown,
    total_amount_kes: Decimal | None = None,
    effective_exchange_rate: Decimal | None = None,
) -> PriceBreakdownOut:  # type: ignore[no-untyped-def]
    return PriceBreakdownOut(
        subtotal_usd=breakdown.subtotal_usd,
        shipping_fee_usd=breakdown.shipping_fee_usd,
        handling_fee_usd=breakdown.handling_fee_usd,
        customs_estimate_usd=breakdown.customs_estimate_usd,
        discount_usd=breakdown.discount_usd,
        total_amount_usd=breakdown.total_amount_usd,
        total_weight_grams=breakdown.total_weight_grams,
        total_amount_kes=total_amount_kes,
        effective_exchange_rate=effective_exchange_rate,
    )


@router.post("/checkout/summary", response_model=PriceBreakdownOut)
async def checkout_summary(payload: CheckoutSummaryRequest, db: AsyncSession = Depends(get_db)) -> PriceBreakdownOut:
    try:
        result = await cart_breakdown_service.calculate_cart_breakdown(
            db,
            [
                cart_breakdown_service.CartLineInput(
                    product_id=item.product_id, variant_id=item.variant_id, quantity=item.quantity
                )
                for item in payload.items
            ],
            payload.country_code,
            payload.discount_code,
        )
    except (cart_breakdown_service.ShippingRuleNotFoundError, cart_breakdown_service.ProductNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    effective_rate, _, _, _ = await get_effective_usd_to_kes_rate(db)
    total_amount_kes = convert_usd_to_kes(result.breakdown.total_amount_usd, effective_rate)

    return _to_breakdown_out(
        result.breakdown,
        total_amount_kes=total_amount_kes,
        effective_exchange_rate=effective_rate,
    )


@router.post("/pricing/calculate", response_model=PriceBreakdownOut)
async def calculate_single_product_price(
    payload: PriceCalculateRequest, db: AsyncSession = Depends(get_db)
) -> PriceBreakdownOut:
    """Single product/variant price preview (not a full cart) - used by the
    product detail page's live calculator widget."""
    product = await db.get(Product, payload.product_id, options=[selectinload(Product.supplier)])
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    variant: ProductVariant | None = None
    if payload.variant_id is not None:
        variant = await db.get(ProductVariant, payload.variant_id)

    shipping_rule = await db.scalar(
        select(CountryShippingRule).where(CountryShippingRule.country_code == payload.country_code)
    )
    if shipping_rule is None:
        raise HTTPException(status_code=400, detail=f"No shipping rule configured for country {payload.country_code}")

    settings = await get_pricing_settings(db)
    discount = await find_active_discount_code(db, payload.discount_code) if payload.discount_code else None

    unit_price_usd = Decimal(product.base_price_usd) + (Decimal(variant.price_delta_usd) if variant else Decimal(0))
    weight_per_unit = variant.weight_override_grams if variant and variant.weight_override_grams else product.base_weight_grams
    margin_pct = Decimal(product.supplier.default_margin_pct) or Decimal(settings.commission_pct)

    breakdown = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=unit_price_usd, quantity=payload.quantity, margin_pct=margin_pct)],
            total_weight_grams=weight_per_unit * payload.quantity,
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

    return _to_breakdown_out(breakdown)
