from fastapi import APIRouter

from app.api.v1.endpoints import ingestion, chat

router = APIRouter(prefix="/api/v1")

router.include_router(ingestion.router, prefix="/documents", tags=["ingestion"])
router.include_router(chat.router, prefix="/chat", tags=["conversation"])
