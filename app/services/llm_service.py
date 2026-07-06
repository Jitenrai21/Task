from __future__ import annotations

import json

from groq import AsyncGroq

from app.core.config import get_settings

settings = get_settings()

_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    """Return the singleton Groq async client."""
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


async def chat_completion(messages: list[dict[str, str]]) -> str:
    """Send *messages* to Groq and return the assistant reply as plain text."""
    client = get_groq_client()
    response = await client.chat.completions.create(
        model=settings.GROQ_CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


async def extract_booking_from_text(conversation_text: str) -> dict | None:
    """Ask Groq to extract structured booking details from a conversation snippet.

    Returns a dict with keys: name, email, interview_date (YYYY-MM-DD),
    interview_time (HH:MM) — or None if a complete booking is not detectable.
    """
    client = get_groq_client()

    extraction_messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a data extraction assistant. "
                "Extract interview booking information from the provided text. "
                "Return ONLY a valid JSON object with exactly these keys: "
                "name (string), email (string), interview_date (YYYY-MM-DD), "
                "interview_time (HH:MM). "
                "If any required field is missing or the text contains no booking, "
                "return the JSON: {}"
            ),
        },
        {"role": "user", "content": conversation_text},
    ]

    response = await client.chat.completions.create(
        model=settings.GROQ_CHAT_MODEL,
        messages=extraction_messages,
        temperature=0.0,
        max_tokens=256,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    try:
        data: dict = json.loads(content)
        required = {"name", "email", "interview_date", "interview_time"}
        if required.issubset(data.keys()) and all(data[k] for k in required):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None
