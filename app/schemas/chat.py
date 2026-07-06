from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    session_id: str = Field(
        description="Unique session identifier — reuse the same ID across turns for multi-turn memory."
    )
    query: str = Field(description="User message / question.")
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve as context.",
    )


class BookingDetail(BaseModel):
    name: str
    email: str
    interview_date: date
    interview_time: time


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str] = Field(
        default_factory=list,
        description="Chunk texts used as retrieved context for this response.",
    )
    booking: BookingDetail | None = Field(
        default=None,
        description="Populated when an interview booking was detected and saved.",
    )
