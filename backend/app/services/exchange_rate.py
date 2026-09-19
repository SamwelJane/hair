"""USD to KES Exchange Rate Service.

Dual-Engine Conversion Architecture:
1. Real-Time API: Fetches live market USD -> KES rate from open exchange rates,
   cached for 1 hour, with a flat +Ksh 4.00 spread per dollar added on top.
2. Admin Configured Rate: Reads the manual USD -> KES rate set in the exchange_rates table.
3. Selection: Evaluates both behind the scenes and picks max(live_rate + 4.00, admin_rate).
4. Cent Precision: Exact rounding to cents (e.g. $200 @ 135.00 -> KES 27,000.00).
"""

from __future__ import annotations

import time
from decimal import ROUND_HALF_UP, Decimal

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import ExchangeRate

log = structlog.get_logger(__name__)

# In-memory cache for live FX rate (1 hour TTL)
_LIVE_CACHE_TTL_SECONDS = 3600
_cached_live_rate: Decimal | None = None
_cached_live_at: float = 0.0

# Public reliable free FX rate API (no key required, fast CDN)
_LIVE_FX_URL = "https://open.er-api.com/v6/latest/USD"

# Default fallback if both live API and admin DB rate are unreachable
_DEFAULT_FALLBACK_RATE = Decimal("130.00")
_DEFAULT_SPREAD_PER_DOLLAR = Decimal("4.00")


class ExchangeRateNotSetError(Exception):
    pass


async def fetch_live_usd_to_kes_rate() -> Decimal:
    """Fetch live USD -> KES market rate with 1-hour in-memory cache and fallback."""
    global _cached_live_rate, _cached_live_at

    now = time.time()
    if _cached_live_rate is not None and (now - _cached_live_at) < _LIVE_CACHE_TTL_SECONDS:
        return _cached_live_rate

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(_LIVE_FX_URL)
            if resp.status_code == 200:
                data = resp.json()
                kes_rate = data.get("rates", {}).get("KES")
                if kes_rate:
                    parsed = Decimal(str(kes_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    _cached_live_rate = parsed
                    _cached_live_at = now
                    log.info("exchange_rate.live_fetched", rate=str(parsed))
                    return parsed
    except Exception as exc:
        log.warning("exchange_rate.live_fetch_failed", error=str(exc))

    # Return cached value if available, else fallback
    return _cached_live_rate or _DEFAULT_FALLBACK_RATE


async def get_admin_usd_to_kes_rate(db: AsyncSession) -> Decimal:
    """Reads the admin-configured USD -> KES rate from the database."""
    rate = await db.scalar(
        select(ExchangeRate).where(
            ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == "KES"
        )
    )
    if rate is None:
        return _DEFAULT_FALLBACK_RATE
    return Decimal(str(rate.rate))


async def get_usd_to_kes_rate(db: AsyncSession) -> Decimal:
    """Returns the effective USD -> KES rate by selecting the maximum between
    (Live Market Rate + Ksh 4.00) and the Admin-set rate.
    """
    effective_rate, _, _, _ = await get_effective_usd_to_kes_rate(db)
    return effective_rate


async def get_effective_usd_to_kes_rate(
    db: AsyncSession,
) -> tuple[Decimal, Decimal, Decimal, str]:
    """Evaluates both conversion approaches and selects the maximum.

    Returns:
        (effective_rate, live_rate_with_spread, admin_rate, selected_strategy)
    """
    live_market_rate = await fetch_live_usd_to_kes_rate()
    live_with_spread = (live_market_rate + _DEFAULT_SPREAD_PER_DOLLAR).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    admin_rate = await get_admin_usd_to_kes_rate(db)

    if live_with_spread >= admin_rate:
        effective_rate = live_with_spread
        selected_strategy = "LIVE_API_PLUS_SPREAD"
    else:
        effective_rate = admin_rate
        selected_strategy = "ADMIN_RATE"

    log.info(
        "exchange_rate.evaluated",
        effective=str(effective_rate),
        live_with_spread=str(live_with_spread),
        admin_rate=str(admin_rate),
        strategy=selected_strategy,
    )
    return effective_rate, live_with_spread, admin_rate, selected_strategy


def convert_usd_to_kes(
    amount_usd: Decimal,
    rate: Decimal,
    adjustment: Decimal = Decimal("0"),
) -> Decimal:
    """Converts USD to KES using the effective rate and returns exact cents.
    
    Formula:
        total_cents = round(amount_usd * (rate + adjustment) * 100)
        return total_cents / 100.00
    """
    effective = rate + adjustment
    cents = int((amount_usd * effective * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
