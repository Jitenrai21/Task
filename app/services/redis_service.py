import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return the singleton Redis async client (lazy-initialised)."""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _client
