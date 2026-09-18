import logging

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: ArqRedis | None = None


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def get_arq_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings())
    return _pool


async def enqueue_notify_supplier_new_order(supplier_order_id: str) -> None:
    """Enqueuing a notification must never be able to block the state
    transition that triggered it - if Redis is unreachable, log and move on
    rather than raising, matching the fail-open pattern used for rate
    limiting. Notifications are a nice-to-have; order/supplier-order status
    changes are not."""
    try:
        pool = await get_arq_pool()
        await pool.enqueue_job("notify_supplier_new_order", supplier_order_id)
    except Exception:  # noqa: BLE001 - deliberately fail-open, see docstring
        logger.warning("Failed to enqueue notify_supplier_new_order for %s - continuing without it", supplier_order_id)


async def enqueue_notify_supplier_status_change(supplier_order_id: str, to_status: str) -> None:
    try:
        pool = await get_arq_pool()
        await pool.enqueue_job("notify_supplier_status_change", supplier_order_id, to_status)
    except Exception:  # noqa: BLE001 - deliberately fail-open, see docstring above
        logger.warning(
            "Failed to enqueue notify_supplier_status_change for %s - continuing without it", supplier_order_id
        )
