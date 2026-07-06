import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import ChunkingStrategy


class IngestResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    file_type: str
    chunking_strategy: ChunkingStrategy
    chunk_count: int = Field(description="Number of chunks stored in the vector store")
    collection_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    document_id: uuid.UUID
    filename: str
    file_type: str
    chunking_strategy: ChunkingStrategy
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
