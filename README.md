# FastAPI Conversational RAG Backend

A production-style backend that supports:

- Document ingestion for PDF and TXT files
- Custom chunking (fixed-size and sentence-based)
- Local embeddings using sentence-transformers
- Vector storage and retrieval in Qdrant
- Multi-turn conversational RAG using Redis session memory
- Groq-powered chat responses
- Interview booking detection and persistence in PostgreSQL

This repository implements a modular, typed FastAPI service with no RetrievalQAChain dependency.

## Project Demonstration

![Project Demo](task_demo.gif)

## System Architecture

- API layer: FastAPI routes for ingestion and chat
- Embedding layer: sentence-transformers local model
- Vector database: Qdrant
- Session memory: Redis
- Relational storage: PostgreSQL (documents metadata and interview bookings)
- LLM layer: Groq chat completions

Request flow for chat:

1. Load prior chat history by session_id from Redis
2. Embed incoming query
3. Retrieve top-k relevant chunks from Qdrant
4. Build prompt manually (system + context + history + user query)
5. Call Groq model
6. Detect and extract booking details
7. Save booking to PostgreSQL (if complete)
8. Save current turn back to Redis

## Project Structure

```text
app/
  api/v1/endpoints/
    ingestion.py
    chat.py
  core/
    config.py
    dependencies.py
    exceptions.py
  db/
    base.py
    session.py
  models/
    document.py
    booking.py
  schemas/
    document.py
    chat.py
    booking.py
  services/
    ingestion_service.py
    embedding_service.py
    retrieval_service.py
    chat_memory.py
    llm_service.py
    booking_service.py
    rag_service.py
  utils/
    chunking.py
alembic/
docker-compose.yml
requirements.txt
```

## API Endpoints

- GET /
  - Returns service status message
- GET /health
  - Returns health/version status
- POST /api/v1/documents/ingest
  - Upload PDF or TXT, chunk, embed, upsert to Qdrant, save metadata in PostgreSQL
- POST /api/v1/chat/
  - Session-aware conversational RAG with optional booking extraction and persistence
- GET /docs
  - Swagger UI

## Prerequisites

- Python 3.11+ (3.12 is fine)
- Docker Desktop (running)
- Git

## Environment Setup

Create a .env file in the repository root.

Example values:

```env
APP_NAME=RAG Backend
APP_VERSION=1.0.0
DEBUG=false

DATABASE_URL=postgresql+asyncpg://postgres:password@127.0.0.1:5433/ragdb
REDIS_URL=redis://localhost:6379/0

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=documents

EMBEDDING_PROVIDER=sentence_transformers
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

CHAT_MEMORY_TTL=3600
```

Security note:

- Never commit .env
- If any real key has been exposed in history, rotate it immediately

## Run the Project (Dockerized Infra + Local API)

### 1. Start infrastructure services

```powershell
docker compose up -d
```

This starts:

- PostgreSQL on host port 5433
- Redis on host port 6379
- Qdrant on host port 6333

### 2. Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run DB migrations

```powershell
alembic upgrade head
```

### 5. Start API server

```powershell
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000/docs

## Usage Examples (PowerShell)

Use curl.exe in PowerShell so multipart upload works as expected.

### Ingest: fixed-size chunking

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/ingest?strategy=fixed_size&chunk_size=500&overlap=50" -F "file=@sample.pdf"
```

### Ingest: sentence chunking

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents/ingest?strategy=sentence&chunk_size=5&overlap=1" -F "file=@sample.txt"
```

### Chat turn 1

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/chat/" -H "Content-Type: application/json" -d '{"session_id":"sess-001","query":"What are the main topics in the ingested document?","top_k":5}'
```

### Chat turn 2 (same session, multi-turn)

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/chat/" -H "Content-Type: application/json" -d '{"session_id":"sess-001","query":"Please summarize in 3 bullets and book an interview for John Doe, john@example.com on 2026-07-20 at 10:00","top_k":5}'
```

Expected chat response includes:

- answer
- sources (retrieved chunks)
- booking (only when complete booking details are detected)

## Inspect Stored Data

### PostgreSQL: documents metadata

```powershell
docker exec -it rag_postgres psql -U postgres -d ragdb -c "SELECT id, filename, file_type, chunking_strategy, chunk_count, created_at FROM documents ORDER BY created_at DESC LIMIT 10;"
```

### PostgreSQL: interview bookings

```powershell
docker exec -it rag_postgres psql -U postgres -d ragdb -c "SELECT id, session_id, name, email, interview_date, interview_time, created_at FROM interview_bookings ORDER BY created_at DESC LIMIT 10;"
```

### Qdrant: collection details

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:6333/collections/documents" | ConvertTo-Json -Depth 10
```

### Qdrant: sample points

```powershell
$body = @{
  limit = 5
  with_payload = $true
  with_vector = $false
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:6333/collections/documents/points/scroll" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
```

## Troubleshooting

### /docs returns 404

- Confirm uvicorn is serving this repository:
  - uvicorn app.main:app --reload
- Verify:
  - GET /health should return status ok

### Failed to connect to Docker engine on Windows

- Start Docker Desktop and wait for engine running
- Retry docker compose up -d

### Alembic: Target database is not up to date

- Run:

```powershell
alembic upgrade head
```

Then create a new revision if needed.

### PostgreSQL authentication failed

- Ensure DATABASE_URL matches docker-compose exposed port (5433)
- Use 127.0.0.1 instead of localhost in DATABASE_URL

## Development Notes

- The app uses custom retrieval and prompt composition.
- No RetrievalQAChain is used.
- Embeddings are generated locally with sentence-transformers.
- Vector payload stores chunk text and metadata for explainable retrieval.