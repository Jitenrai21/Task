# Import all models here so that:
#  1. Alembic's env.py can discover every table via Base.metadata
#  2. SQLAlchemy's mapper registry is populated before the engine is used
from app.models.booking import InterviewBooking  # noqa: F401
from app.models.document import ChunkingStrategy, Document  # noqa: F401

__all__ = ["Document", "ChunkingStrategy", "InterviewBooking"]
