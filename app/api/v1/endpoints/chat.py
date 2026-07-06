from __future__ import annotations

from datetime import date, time

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_embedding_service,
    get_redis,
    get_vector_store,
)
from app.schemas.chat import BookingDetail, ChatRequest, ChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import run_rag

router = APIRouter()


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Conversational RAG chat",
    description=(
        "Send a message with a `session_id` to start or continue a multi-turn "
        "conversation. The assistant retrieves relevant document chunks, builds a "
        "grounded response via Groq LLM, and automatically detects + stores "
        "interview booking requests.\n\n"
        "Reuse the same `session_id` across requests to maintain conversation history."
    ),
)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_vector_store),
    redis: aioredis.Redis = Depends(get_redis),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> ChatResponse:
    result = await run_rag(
        session_id=request.session_id,
        user_query=request.query,
        embedding_svc=embedding_svc,
        qdrant=qdrant,
        redis=redis,
        db=db,
        top_k=request.top_k,
    )

    booking: BookingDetail | None = None
    if result.booking_data:
        booking = BookingDetail(
            name=result.booking_data["name"],
            email=result.booking_data["email"],
            interview_date=date.fromisoformat(result.booking_data["interview_date"]),
            interview_time=time.fromisoformat(
                result.booking_data["interview_time"]
                if len(result.booking_data["interview_time"]) > 5
                else result.booking_data["interview_time"] + ":00"
            ),
        )

    return ChatResponse(
        session_id=request.session_id,
        answer=result.answer,
        sources=result.sources,
        booking=booking,
    )
