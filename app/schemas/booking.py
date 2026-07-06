import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    name: str
    email: str
    interview_date: date
    interview_time: time


class BookingResponse(BookingCreate):
    id: uuid.UUID
    session_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
