from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import DiscountCode, PricingSetting


async def get_pricing_settings(db: AsyncSession) -> PricingSetting:
    """Single source of truth for the global pricing settings row - both the
    real checkout path and the price-preview endpoints must load this the
    same way, or their totals silently disagree. Upserts the singleton row
    with defaults if it doesn't exist yet, mirroring the old app's
    `db.pricingSetting.upsert(...)`."""
    existing = await db.get(PricingSetting, "global")
    if existing is not None:
        return existing

    stmt = insert(PricingSetting).values(id="global").on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()
    return await db.get(PricingSetting, "global")  # type: ignore[return-value]


async def find_active_discount_code(db: AsyncSession, code: str) -> DiscountCode | None:
    """Resolves a discount code, honoring expiry and usage-limit in addition
    to `active` - a plain `active: true` filter alone lets an expired or
    already-maxed-out code keep discounting indefinitely."""
    discount = await db.scalar(select(DiscountCode).where(DiscountCode.code == code, DiscountCode.active.is_(True)))
    if discount is None:
        return None
    if discount.expires_at is not None and discount.expires_at < datetime.now(UTC):
        return None
    if discount.usage_limit is not None and discount.times_used >= discount.usage_limit:
        return None
    return discount
