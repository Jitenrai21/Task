from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.core.config import get_settings
from app.core.exceptions import (
    DocumentNotFoundError,
    EmbeddingError,
    UnsupportedFileTypeError,
    VectorStoreError,
    document_not_found_handler,
    embedding_error_handler,
    unsupported_file_type_handler,
    vector_store_error_handler,
)
from app.services.redis_service import get_redis_client
from app.services.vector_store import ensure_collection_exists, get_qdrant_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup 
    qdrant = get_qdrant_client()
    await ensure_collection_exists(qdrant)
    get_redis_client()  # initialise singleton
    yield
    # Shutdown 
    # Clients handle their own cleanup via context managers/GC


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers 
app.add_exception_handler(DocumentNotFoundError, document_not_found_handler)
app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_type_handler)
app.add_exception_handler(VectorStoreError, vector_store_error_handler)
app.add_exception_handler(EmbeddingError, embedding_error_handler)

# Routers 
app.include_router(router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"message": "service is running"}

# Health check 
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": settings.APP_VERSION}
