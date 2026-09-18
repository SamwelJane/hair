from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


def _round2(value: Decimal) -> Decimal:
    """Matches the old app's Math.round(value * 100) / 100 - round-half-up,
    not banker's rounding, so money always rounds the same way a customer
    would expect (and the same way the JS engine did)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class PriceLineItem:
    unit_price_usd: Decimal
    quantity: int
    # Per-line commission %, driven by that line's supplier margin. Falls
    # back to the top-level commission_pct (the platform default) when None.
    margin_pct: Decimal | None = None


@dataclass
class ShippingRuleInput:
    base_fee_usd: Decimal
    per_kg_fee_usd: Decimal
    customs_rate_pct: Decimal


@dataclass
class DiscountCodeInput:
    type: str  # "percent" | "fixed"
    value: Decimal
    min_order_usd: Decimal | None = None


@dataclass
class PriceBreakdown:
    subtotal_usd: Decimal
    shipping_fee_usd: Decimal
    handling_fee_usd: Decimal
    customs_estimate_usd: Decimal
    discount_usd: Decimal
    total_amount_usd: Decimal
    total_weight_grams: int
    supplier_subtotal_usd: Decimal = Decimal(0)
    platform_margin_usd: Decimal = Decimal(0)
    packaging_fee_usd: Decimal = Decimal(2)


@dataclass
class CalculatePriceInput:
    items: list[PriceLineItem]
    total_weight_grams: int
    shipping_rule: ShippingRuleInput | None = None
    handling_fee_usd: Decimal = Decimal(0)
    commission_pct: Decimal | None = Decimal(15)  # 15% platform markup by default
    shipping_per_kg_usd: Decimal | None = Decimal(60)  # $60/kg flat air freight & customs
    packaging_fee_usd: Decimal | None = Decimal(2)  # $2 flat packaging per order
    discount_code: DiscountCodeInput | None = None


def calculate_price(input: CalculatePriceInput) -> PriceBreakdown:
    """Calculates all-inclusive landed cost:
    - Product storefront price = supplier price * 1.15 (15% platform markup)
    - Weight: total_weight_grams / 1000 = weight_kg
    - Shipping fee = weight_kg * $60/kg + $2 packaging fee
    - Customs estimate = 0 (all-inclusive flat freight & customs rate)
    - Platform margin = 15% markup + $2 packaging fee
    """
    supplier_subtotal = _round2(sum((item.unit_price_usd * item.quantity for item in input.items), Decimal(0)))

    # Apply 15% platform markup if not already marked up
    markup_pct = input.commission_pct if input.commission_pct is not None else Decimal(15)
    markup_multiplier = Decimal(1) + (markup_pct / Decimal(100))
    subtotal_usd = _round2(supplier_subtotal * markup_multiplier)

    # Shipping at $60/kg + $2 packaging fee
    weight_kg = Decimal(input.total_weight_grams) / Decimal(1000)
    per_kg_rate = input.shipping_per_kg_usd if input.shipping_per_kg_usd is not None else Decimal(60)
    packaging_fee = input.packaging_fee_usd if input.packaging_fee_usd is not None else Decimal(2)
    shipping_fee_usd = _round2(per_kg_rate * weight_kg + packaging_fee)

    customs_estimate_usd = Decimal(0)
    handling_fee_usd = Decimal(0)

    discount_usd = Decimal(0)
    if input.discount_code is not None:
        min_order = input.discount_code.min_order_usd or Decimal(0)
        if subtotal_usd >= min_order:
            if input.discount_code.type == "percent":
                discount_usd = _round2(subtotal_usd * (input.discount_code.value / Decimal(100)))
            else:
                discount_usd = _round2(input.discount_code.value)

    total_amount_usd = _round2(
        max(
            Decimal(0),
            subtotal_usd + shipping_fee_usd - discount_usd,
        )
    )

    platform_margin_usd = _round2((subtotal_usd - supplier_subtotal) + packaging_fee)

    return PriceBreakdown(
        subtotal_usd=subtotal_usd,
        shipping_fee_usd=shipping_fee_usd,
        handling_fee_usd=handling_fee_usd,
        customs_estimate_usd=customs_estimate_usd,
        discount_usd=discount_usd,
        total_amount_usd=total_amount_usd,
        total_weight_grams=input.total_weight_grams,
        supplier_subtotal_usd=supplier_subtotal,
        platform_margin_usd=platform_margin_usd,
        packaging_fee_usd=packaging_fee,
    )
