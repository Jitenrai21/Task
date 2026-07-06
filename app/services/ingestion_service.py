from __future__ import annotations

import json
import uuid

import fitz  # PyMuPDF
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError, UnsupportedFileTypeError, VectorStoreError
from app.models.document import ChunkingStrategy, Document
from app.services.embedding_service import EmbeddingService
from app.utils.chunking import TextChunk, fixed_size_chunks, sentence_chunks

settings = get_settings()

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "txt"})

# Text extraction 
def _extract_text_from_pdf(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages).strip()


def _extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="replace").strip()


def extract_text(content: bytes, filename: str) -> str:
    """Return plain text extracted from a PDF or TXT file."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(ext)
    if ext == "pdf":
        return _extract_text_from_pdf(content)
    return _extract_text_from_txt(content)


# Chunking dispatch
def chunk_text(
    text: str,
    strategy: ChunkingStrategy,
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    """Dispatch text to the selected chunking strategy.

    For FIXED_SIZE:  chunk_size = characters per chunk, overlap = character overlap.
    For SENTENCE:    chunk_size = max sentences per chunk, overlap = sentence overlap.
    """
    if strategy == ChunkingStrategy.FIXED_SIZE:
        return fixed_size_chunks(text, chunk_size=chunk_size, overlap=overlap)
    return sentence_chunks(text, max_sentences=chunk_size, overlap_sentences=overlap)


# Main ingestion orchestrator
async def ingest_document(
    *,
    content: bytes,
    filename: str,
    strategy: ChunkingStrategy,
    chunk_size: int,
    overlap: int,
    embedding_svc: EmbeddingService,
    qdrant: AsyncQdrantClient,
    db: AsyncSession,
) -> Document:
    """Full pipeline: extract → chunk → embed → upsert → persist metadata."""

    # 1. Extract text
    text = extract_text(content, filename)
    if not text:
        raise ValueError("No extractable text found in the uploaded file.")

    # 2. Chunk
    chunks = chunk_text(text, strategy, chunk_size, overlap)
    if not chunks:
        raise ValueError("Chunking produced no content. Try a smaller chunk size.")

    # 3. Embed (batched)
    chunk_texts = [c.text for c in chunks]
    try:
        embeddings = await embedding_svc.embed_texts(chunk_texts)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(f"Unexpected embedding failure: {exc}") from exc

    # 4. Upsert to Qdrant
    doc_id = uuid.uuid4()
    file_type = filename.rsplit(".", 1)[-1].lower()

    points: list[PointStruct] = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "document_id": str(doc_id),
                "filename": filename,
                "file_type": file_type,
                "chunk_index": chunk.index,
                "text": chunk.text,
                "strategy": strategy.value,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    try:
        await qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points,
            wait=True,
        )
    except Exception as exc:
        raise VectorStoreError(f"Qdrant upsert failed: {exc}") from exc

    # 5. Persist metadata to PostgreSQL
    document = Document(
        id=doc_id,
        filename=filename,
        file_type=file_type,
        chunking_strategy=strategy,
        chunk_count=len(chunks),
        vector_ids=json.dumps([p.id for p in points]),
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )
    db.add(document)
    await db.flush()  # commit is handled by the get_db() dependency

    return document
