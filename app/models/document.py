import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChunkingStrategy(str, enum.Enum):
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "pdf" | "txt"
    chunking_strategy: Mapped[ChunkingStrategy] = mapped_column(
        SAEnum(ChunkingStrategy, name="chunkingstrategy"), nullable=False
    )
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # JSON-serialised list of Qdrant point UUIDs, e.g. '["uuid1","uuid2"]'
    vector_ids: Mapped[str] = mapped_column(Text, nullable=False)
    collection_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename!r}>"
