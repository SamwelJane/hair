from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import ExchangeRate


class ExchangeRateNotSetError(Exception):
    pass


async def get_usd_to_kes_rate(db: AsyncSession) -> Decimal:
    """Reads the admin-set USD -> KES rate. No live FX API call here by
    design: the admin sets the rate in the settings UI and that is the rate
    charged to customers at checkout, regardless of the real market rate."""
    rate = await db.scalar(
        select(ExchangeRate).where(
            ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == "KES"
        )
    )
    if rate is None:
        raise ExchangeRateNotSetError("No USD->KES exchange rate has been set by an admin yet.")
    return Decimal(rate.rate)


def convert_usd_to_kes(amount_usd: Decimal, rate: Decimal, adjustment: Decimal) -> Decimal:
    """`adjustment` has no default here, unlike the old app's
    convertUsdToKes(amountUsd, rate, adjustment = 4) - every caller is
    required to pass the value read from PricingSetting.kes_adjustment, which
    closes a real inconsistency in the old app (the checkout flow there
    called this without passing the configured adjustment, silently using
    the hardcoded default of 4 instead of whatever the admin had set)."""
    return (amount_usd * (rate + adjustment)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
