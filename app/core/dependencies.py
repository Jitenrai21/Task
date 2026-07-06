from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from groq import AsyncGroq

from app.services.embedding_service import EmbeddingService
from app.services.embedding_service import get_embedding_service as _get_embedding_service
from app.services.redis_service import get_redis_client
from app.services.vector_store import get_qdrant_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields an async DB session with automatic commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_vector_store() -> AsyncQdrantClient:
    """Returns the singleton Qdrant async client."""
    return get_qdrant_client()


def get_redis() -> aioredis.Redis:
    """Returns the singleton Redis async client."""
    return get_redis_client()


def get_embedding_service() -> EmbeddingService:
    """Returns the singleton EmbeddingService (sentence-transformers, local)."""
    return _get_embedding_service()


def get_llm_client() -> AsyncGroq:
    """Returns the singleton Groq async client."""
    from app.services.llm_service import get_groq_client
    return get_groq_client()
