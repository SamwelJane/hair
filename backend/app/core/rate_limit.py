from functools import lru_cache

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def _redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)


async def rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Fixed-window counter, direct port of src/lib/security/rate-limit.ts.
    Fails OPEN (returns True/allowed) if Redis is unreachable or errors -
    rate limiting is explicitly best-effort here, not a hard security
    boundary, matching the old app's documented behavior."""
    try:
        client = _redis_client()
        full_key = f"ratelimit:{key}"
        count = await client.incr(full_key)
        if count == 1:
            await client.expire(full_key, window_seconds)
        return count <= limit
    except Exception:  # noqa: BLE001 - deliberately fail-open on ANY Redis error
        return True


def get_client_ip(headers: dict[str, str], client_host: str | None) -> str:
    forwarded_for = headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return client_host or "unknown"
