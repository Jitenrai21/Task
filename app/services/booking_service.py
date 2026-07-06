from __future__ import annotations

from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookingExtractionError
from app.models.booking import InterviewBooking


async def save_booking(
    *,
    session_id: str,
    data: dict,
    db: AsyncSession,
) -> InterviewBooking:
    """Validate and persist interview booking extracted from LLM output."""
    try:
        interview_date = date.fromisoformat(data["interview_date"])
        # Accept HH:MM or HH:MM:SS formats
        time_raw: str = data["interview_time"]
        if len(time_raw) == 5:
            time_raw += ":00"
        interview_time = time.fromisoformat(time_raw)
    except (KeyError, ValueError) as exc:
        raise BookingExtractionError(
            f"Could not parse booking fields: {exc}"
        ) from exc

    booking = InterviewBooking(
        session_id=session_id,
        name=str(data["name"]).strip(),
        email=str(data["email"]).strip().lower(),
        interview_date=interview_date,
        interview_time=interview_time,
    )
    db.add(booking)
    await db.flush()
    return booking
