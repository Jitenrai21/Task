from __future__ import annotations

import asyncio
from typing import Sequence

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

        if self.provider not in {"sentence_transformers"}:
            raise EmbeddingError(
                "Invalid EMBEDDING_PROVIDER. Use 'sentence_transformers'."
            )

        self._local_model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
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
