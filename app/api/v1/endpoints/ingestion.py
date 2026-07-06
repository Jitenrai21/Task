from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_embedding_service, get_vector_store
from app.models.document import ChunkingStrategy
from app.schemas.document import IngestResponse
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import ingest_document

router = APIRouter()

_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({"application/pdf", "text/plain"})
_MAX_FILE_MB = 20


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a PDF or TXT document",
    description=(
        "Upload a `.pdf` or `.txt` file. The service extracts text, applies the "
        "selected chunking strategy, generates embeddings, stores vectors in Qdrant, "
        "and persists document metadata in PostgreSQL.\n\n"
        "**chunk_size / overlap semantics by strategy:**\n"
        "- `fixed_size` — chunk_size = characters per chunk (default 500), "
        "overlap = character overlap (default 50).\n"
        "- `sentence` — chunk_size = max sentences per chunk (default 5), "
        "overlap = sentence overlap (default 1)."
    ),
)
async def ingest(
    file: UploadFile = File(..., description="PDF or TXT file"),
    strategy: ChunkingStrategy = Query(
        default=ChunkingStrategy.FIXED_SIZE,
        description="Chunking strategy: `fixed_size` or `sentence`",
    ),
    chunk_size: int = Query(
        default=500,
        ge=1,
        le=5000,
        description="Characters per chunk (fixed_size) or max sentences per chunk (sentence)",
    ),
    overlap: int = Query(
        default=50,
        ge=0,
        le=1000,
        description="Character overlap (fixed_size) or sentence overlap (sentence)",
    ),
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_vector_store),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> IngestResponse:
    # File size guard 
    content = await file.read()
    if len(content) > _MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {_MAX_FILE_MB} MB.",
        )

    # Ingest pipeline
    document = await ingest_document(
        content=content,
        filename=file.filename or "unnamed",
        strategy=strategy,
        chunk_size=chunk_size,
        overlap=overlap,
        embedding_svc=embedding_svc,
        qdrant=qdrant,
        db=db,
    )

    return IngestResponse(
        document_id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        chunking_strategy=document.chunking_strategy,
        chunk_count=document.chunk_count,
        collection_name=document.collection_name,
        created_at=document.created_at,
    )
