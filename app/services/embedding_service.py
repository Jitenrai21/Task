from __future__ import annotations

import asyncio
from typing import Sequence

from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError

settings = get_settings()


class EmbeddingService:
    """Provider-aware embedding service.

    Supports:
    - sentence_transformers (free, local)
    - openai (fallback)
    """

    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER.lower().strip()
        self._local_model: SentenceTransformer | None = None
        self._openai_client: AsyncOpenAI | None = None

        if self.provider not in {"sentence_transformers", "openai"}:
            raise EmbeddingError(
                "Invalid EMBEDDING_PROVIDER. Use 'sentence_transformers' or 'openai'."
            )

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise EmbeddingError(
                    "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai."
                )
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self._local_model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            if self.provider == "openai":
                assert self._openai_client is not None
                response = await self._openai_client.embeddings.create(
                    model=settings.OPENAI_EMBEDDING_MODEL,
                    input=list(texts),
                )
                return [item.embedding for item in response.data]

            assert self._local_model is not None
            vectors = await asyncio.to_thread(
                self._local_model.encode,
                list(texts),
                normalize_embeddings=True,
            )
            return [vector.tolist() for vector in vectors]
        except Exception as exc:
            raise EmbeddingError(f"Failed to generate embeddings: {exc}") from exc


_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
