from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import CountryShippingRule


class DeliveryEstimate:
    def __init__(self, min_days: int, max_days: int) -> None:
        self.min_days = min_days
        self.max_days = max_days


async def get_delivery_estimate(db: AsyncSession, country_code: str) -> DeliveryEstimate | None:
    rule = (
        await db.execute(select(CountryShippingRule).where(CountryShippingRule.country_code == country_code))
    ).scalar_one_or_none()
    if rule is None:
        return None
    return DeliveryEstimate(min_days=rule.estimated_days_min, max_days=rule.estimated_days_max)
