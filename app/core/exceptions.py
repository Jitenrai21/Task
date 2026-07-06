from fastapi import Request, status
from fastapi.responses import JSONResponse


class DocumentNotFoundError(Exception):
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document '{document_id}' not found")


class UnsupportedFileTypeError(Exception):
    def __init__(self, file_type: str) -> None:
        self.file_type = file_type
        super().__init__(f"Unsupported file type: '{file_type}'. Allowed: pdf, txt")


class VectorStoreError(Exception):
    pass


class EmbeddingError(Exception):
    pass


class BookingExtractionError(Exception):
    pass


# Exception handlers 
async def document_not_found_handler(
    request: Request, exc: DocumentNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def unsupported_file_type_handler(
    request: Request, exc: UnsupportedFileTypeError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        content={"detail": str(exc)},
    )


async def vector_store_error_handler(
    request: Request, exc: VectorStoreError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Vector store is unavailable. Please try again later."},
    )


async def embedding_error_handler(
    request: Request, exc: EmbeddingError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Embedding service failed. Please try again later."},
    )
