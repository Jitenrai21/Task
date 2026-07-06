from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application 
    APP_NAME: str = "RAG Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # PostgreSQL (asyncpg driver)
    DATABASE_URL: str = Field(
        description="postgresql+asyncpg://user:pass@host:port/dbname"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Qdrant 
    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "documents"

    # Embeddings (local, free — sentence-transformers only)
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Groq (LLM chat)
    GROQ_API_KEY: str = Field(description="Groq API key — used for chat completions")
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Embedding
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 default output dimension

    # Chat memory
    CHAT_MEMORY_TTL: int = 3600  # Redis key TTL in seconds


@lru_cache
def get_settings() -> Settings:
    return Settings()
