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


@dataclass
class CalculatePriceInput:
    items: list[PriceLineItem]
    total_weight_grams: int
    shipping_rule: ShippingRuleInput
    handling_fee_usd: Decimal = Decimal(0)
    commission_pct: Decimal | None = None
    shipping_per_kg_usd: Decimal | None = None
    packaging_fee_usd: Decimal | None = None
    discount_code: DiscountCodeInput | None = None


def calculate_price(input: CalculatePriceInput) -> PriceBreakdown:
    """Direct port of src/lib/pricing/engine.ts calculatePrice().

    Total = (unit price * qty) + shipping + handling + customs - discount.
    Shipping = baseFee + perKgFee * weight; customs = customsRatePct% of subtotal.
    Handling's commission is computed per-line (each line's supplier margin,
    falling back to the platform default commission_pct), then summed - not
    one flat percentage of the whole subtotal - so different suppliers'
    margins actually affect what the customer pays, not just internal
    reporting.
    """
    subtotal_usd = _round2(sum((item.unit_price_usd * item.quantity for item in input.items), Decimal(0)))

    weight_kg = Decimal(input.total_weight_grams) / Decimal(1000)
    per_kg_fee = input.shipping_per_kg_usd if input.shipping_per_kg_usd is not None else input.shipping_rule.per_kg_fee_usd
    packaging_fee = input.packaging_fee_usd if input.packaging_fee_usd is not None else Decimal(0)
    shipping_fee_usd = _round2(input.shipping_rule.base_fee_usd + per_kg_fee * weight_kg + packaging_fee)

    commission_usd = _round2(
        sum(
            (
                item.unit_price_usd
                * item.quantity
                * ((item.margin_pct if item.margin_pct is not None else (input.commission_pct or Decimal(0))) / Decimal(100))
                for item in input.items
            ),
            Decimal(0),
        )
    )
    handling_fee_usd = _round2(input.handling_fee_usd + commission_usd)
    customs_estimate_usd = _round2(subtotal_usd * (input.shipping_rule.customs_rate_pct / Decimal(100)))

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
            subtotal_usd + shipping_fee_usd + handling_fee_usd + customs_estimate_usd - discount_usd,
        )
    )

    return PriceBreakdown(
        subtotal_usd=subtotal_usd,
        shipping_fee_usd=shipping_fee_usd,
        handling_fee_usd=handling_fee_usd,
        customs_estimate_usd=customs_estimate_usd,
        discount_usd=discount_usd,
        total_amount_usd=total_amount_usd,
        total_weight_grams=input.total_weight_grams,
    )
