from __future__ import annotations

from dataclasses import dataclass, field

import redis.asyncio as aioredis
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.booking_service import save_booking
from app.services.chat_memory import append_turns, load_history
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import chat_completion, extract_booking_from_text
from app.services.retrieval_service import retrieve_relevant_chunks

# Prompt template 

_SYSTEM_PROMPT = """\
You are a knowledgeable AI assistant with access to a curated document knowledge base.

Guidelines:
- Answer questions using the provided context. Be concise and factual.
- If the context does not contain enough information, say so honestly.
- For multi-turn conversations, maintain continuity with prior messages.

Interview Booking:
- If the user wants to book an interview, guide them to provide: full name, email address, preferred date (YYYY-MM-DD), and preferred time (HH:MM).
- Once all fields are collected, confirm the booking details clearly in your response.\
"""

# Keywords that trigger booking intent detection
_BOOKING_KEYWORDS: frozenset[str] = frozenset({
    "book", "schedule", "interview", "appointment", "reserve", "slot", "meeting",
})

# Maximum number of historical turns included in the prompt (each turn = 2 messages)
_MAX_HISTORY_TURNS = 10


# Result dataclass

@dataclass
class RAGResult:
    answer: str
    sources: list[str] = field(default_factory=list)
    booking_data: dict | None = None


# Helpers

def _has_booking_intent(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _BOOKING_KEYWORDS)


def _build_messages(
    history: list[dict[str, str]],
    context_chunks: list[str],
    user_query: str,
) -> list[dict[str, str]]:
    if context_chunks:
        context_block = "\n\n---\n\n".join(context_chunks)
    else:
        context_block = "No relevant documents found in the knowledge base."

    system_content = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"### RETRIEVED CONTEXT\n{context_block}"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    # Cap history to last N messages to stay within token limits
    messages.extend(history[-_MAX_HISTORY_TURNS * 2:])
    messages.append({"role": "user", "content": user_query})
    return messages


# Main orchestrator

async def run_rag(
    *,
    session_id: str,
    user_query: str,
    embedding_svc: EmbeddingService,
    qdrant: AsyncQdrantClient,
    redis: aioredis.Redis,
    db: AsyncSession,
    top_k: int = 5,
) -> RAGResult:
    """Full RAG pipeline:
    load history → retrieve chunks → build prompt → call LLM
    → detect booking → persist booking → save turn → return result.
    """

    # 1. Load chat history from Redis
    history = await load_history(redis, session_id)

    # 2. Retrieve top-k relevant chunks (custom, no RetrievalQAChain)
    sources = await retrieve_relevant_chunks(
        user_query, embedding_svc, qdrant, top_k=top_k
    )

    # 3. Build prompt manually and call Groq LLM
    messages = _build_messages(history, sources, user_query)
    answer = await chat_completion(messages)

    # 4. Detect booking intent in combined turn
    booking_data: dict | None = None
    combined = f"User: {user_query}\nAssistant: {answer}"

    if _has_booking_intent(combined):
        booking_data = await extract_booking_from_text(combined)

    # 5. Persist booking to PostgreSQL if complete
    if booking_data:
        await save_booking(session_id=session_id, data=booking_data, db=db)

    # 6. Save turn to Redis
    await append_turns(redis, session_id, user_query, answer)

    return RAGResult(answer=answer, sources=sources, booking_data=booking_data)
