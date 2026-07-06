from __future__ import annotations

import json

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

_KEY_PREFIX = "chat:session:"


def _session_key(session_id: str) -> str:
    return f"{_KEY_PREFIX}{session_id}"


async def load_history(
    redis: aioredis.Redis,
    session_id: str,
) -> list[dict[str, str]]:
    """Return all stored turns for *session_id* as a list of role/content dicts."""
    raw: list[str] = await redis.lrange(_session_key(session_id), 0, -1)
    return [json.loads(item) for item in raw]


async def append_turns(
    redis: aioredis.Redis,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Append a user + assistant turn pair and refresh the session TTL."""
    key = _session_key(session_id)
    async with redis.pipeline(transaction=True) as pipe:
        pipe.rpush(key, json.dumps({"role": "user", "content": user_message}))
        pipe.rpush(key, json.dumps({"role": "assistant", "content": assistant_message}))
        pipe.expire(key, settings.CHAT_MEMORY_TTL)
        await pipe.execute()


async def clear_history(redis: aioredis.Redis, session_id: str) -> None:
    """Delete all history for *session_id* (useful for tests / session reset)."""
    await redis.delete(_session_key(session_id))
