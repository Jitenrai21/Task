from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService

settings = get_settings()


async def retrieve_relevant_chunks(
    query: str,
    embedding_svc: EmbeddingService,
    qdrant: AsyncQdrantClient,
    top_k: int = 5,
) -> list[str]:
    """Embed *query* and return the top-k matching chunk texts from Qdrant.

    This is a fully custom retrieval implementation — no LangChain or
    RetrievalQAChain is used anywhere in this pipeline.
    """
    query_vector = await embedding_svc.embed_text(query)

    results = await qdrant.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    chunks: list[str] = [
        hit.payload["text"]
        for hit in results
        if hit.payload and hit.payload.get("text")
    ]
    return chunks
