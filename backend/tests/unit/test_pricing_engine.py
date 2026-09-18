from decimal import Decimal

from app.services.pricing_engine import (
    CalculatePriceInput,
    DiscountCodeInput,
    PriceLineItem,
    ShippingRuleInput,
    calculate_price,
)

RULE = ShippingRuleInput(base_fee_usd=Decimal(10), per_kg_fee_usd=Decimal(5), customs_rate_pct=Decimal(8))


def test_basic_single_line_no_extras():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(100), quantity=1)],
            total_weight_grams=1000,
            shipping_rule=RULE,
        )
    )
    assert result.subtotal_usd == Decimal("100.00")
    # shipping = 10 + 5*1kg = 15
    assert result.shipping_fee_usd == Decimal("15.00")
    assert result.handling_fee_usd == Decimal("0.00")
    # customs = 100 * 8% = 8
    assert result.customs_estimate_usd == Decimal("8.00")
    assert result.discount_usd == Decimal("0.00")
    # total = 100 + 15 + 0 + 8 - 0 = 123
    assert result.total_amount_usd == Decimal("123.00")
    assert result.total_weight_grams == 1000


def test_zero_weight_only_base_fee_applies():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(50), quantity=1)],
            total_weight_grams=0,
            shipping_rule=RULE,
        )
    )
    assert result.shipping_fee_usd == Decimal("10.00")


def test_commission_computed_per_line_using_margin_pct_falls_back_to_commission_pct():
    result = calculate_price(
        CalculatePriceInput(
            items=[
                PriceLineItem(unit_price_usd=Decimal(100), quantity=1, margin_pct=Decimal(20)),
                PriceLineItem(unit_price_usd=Decimal(100), quantity=1, margin_pct=None),
            ],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            commission_pct=Decimal(10),
        )
    )
    # line 1: 100 * 20% = 20; line 2 (no margin_pct): falls back to commission_pct 10% -> 10
    assert result.handling_fee_usd == Decimal("30.00")


def test_flat_handling_fee_added_to_commission():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(100), quantity=1, margin_pct=Decimal(5))],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            handling_fee_usd=Decimal("3.50"),
        )
    )
    # commission = 100*5% = 5; handling = 3.50 + 5 = 8.50
    assert result.handling_fee_usd == Decimal("8.50")


def test_percent_discount_applied_when_subtotal_meets_minimum():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(200), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            discount_code=DiscountCodeInput(type="percent", value=Decimal(10), min_order_usd=Decimal(100)),
        )
    )
    assert result.discount_usd == Decimal("20.00")
    assert result.total_amount_usd == Decimal("180.00")


def test_fixed_discount_applied_when_subtotal_meets_minimum():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(200), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            discount_code=DiscountCodeInput(type="fixed", value=Decimal(15), min_order_usd=Decimal(100)),
        )
    )
    assert result.discount_usd == Decimal("15.00")
    assert result.total_amount_usd == Decimal("185.00")


def test_discount_not_applied_below_minimum_order():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(50), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            discount_code=DiscountCodeInput(type="percent", value=Decimal(10), min_order_usd=Decimal(100)),
        )
    )
    assert result.discount_usd == Decimal("0.00")
    assert result.total_amount_usd == Decimal("50.00")


def test_discount_with_no_minimum_always_applies():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(10), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            discount_code=DiscountCodeInput(type="fixed", value=Decimal(5), min_order_usd=None),
        )
    )
    assert result.discount_usd == Decimal("5.00")


def test_total_clamped_to_zero_when_discount_exceeds_everything_else():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(10), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
            discount_code=DiscountCodeInput(type="fixed", value=Decimal(1000), min_order_usd=None),
        )
    )
    assert result.total_amount_usd == Decimal("0.00")


def test_shipping_per_kg_and_packaging_fee_overrides_take_precedence_over_shipping_rule():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(10), quantity=1)],
            total_weight_grams=1000,
            shipping_rule=RULE,  # per_kg_fee_usd=5
            shipping_per_kg_usd=Decimal(2),  # override
            packaging_fee_usd=Decimal("1.50"),
        )
    )
    # shipping = base(10) + override_per_kg(2)*1kg + packaging(1.5) = 13.50
    assert result.shipping_fee_usd == Decimal("13.50")


def test_shipping_falls_back_to_rule_per_kg_fee_when_no_override_given():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal(10), quantity=1)],
            total_weight_grams=2000,
            shipping_rule=RULE,  # base=10, per_kg=5
        )
    )
    # shipping = 10 + 5*2kg + 0 = 20
    assert result.shipping_fee_usd == Decimal("20.00")


def test_multi_line_subtotal_sums_unit_price_times_quantity():
    result = calculate_price(
        CalculatePriceInput(
            items=[
                PriceLineItem(unit_price_usd=Decimal("19.99"), quantity=3),
                PriceLineItem(unit_price_usd=Decimal("5.005"), quantity=2),
            ],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
        )
    )
    # 19.99*3=59.97, 5.005*2=10.01 (rounds to 10.01 via round-half-up on the summed value)
    assert result.subtotal_usd == Decimal("69.98")


def test_rounding_is_half_up_not_banker_rounding():
    result = calculate_price(
        CalculatePriceInput(
            items=[PriceLineItem(unit_price_usd=Decimal("0.005"), quantity=1)],
            total_weight_grams=0,
            shipping_rule=ShippingRuleInput(base_fee_usd=Decimal(0), per_kg_fee_usd=Decimal(0), customs_rate_pct=Decimal(0)),
        )
    )
    # 0.005 rounds up to 0.01 (round-half-up), not down to 0.00 (banker's rounding would go to even = 0.00)
    assert result.subtotal_usd == Decimal("0.01")
