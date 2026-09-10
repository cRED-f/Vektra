"""FastAPI route handlers — /retrieve, /chat, /ingest, /benchmark, /models, /health, /metrics."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, Response, StreamingResponse
from prometheus_client import generate_latest
from sqlalchemy import text, select, delete as sa_delete

from server.core.db import get_engine, DocumentRow, ChunkRow, get_session_factory

from server.api.auth import verify_token
from server.api.circuit_breaker import get_circuit_breaker
from server.api.ratelimit import get_rate_limiter
from server.core.errors import (
    EmptyCorpusError,
    RetrievalError,
    ServingError,
)
from server.core.logging import get_logger
from server.core.schemas import (
    BenchmarkRequest,
    BenchmarkResult,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RetrievalQuery,
    RetrievalResult,
)
from server.registry.client import RegistryClient
from server.retrieve.retriever import Retriever
from server.serve.server import ModelServer

logger = get_logger("api.routes")

router = APIRouter()

SYSTEM_PROMPT = """You are Vektra, a knowledgeable and helpful AI assistant specialized in answering questions based on provided documentation and context.

Rules:
- Answer ONLY based on the provided context. If the context does not contain enough information, say so clearly.
- Be concise and direct. Use bullet points for multiple items.
- When listing features, steps, or options, use numbered or bulleted lists.
- If the user asks about something not in the context, respond: "I don't have that information in my current knowledge base. Please upload relevant documents or rephrase your question."
- Never fabricate information. Only state what is supported by the context.
- For technical questions, include specific details from the context (file names, function names, config values).
- Maintain a professional but friendly tone.
- When the user uploads files, confirm the upload and summarize what was ingested.
"""


# ── Dependencies ───────────────────────────────────────────────────────

def get_retriever() -> Retriever:
    return Retriever()


def get_model_server() -> ModelServer:
    return ModelServer()


def get_registry() -> RegistryClient:
    return RegistryClient()


# ── Rate limit check ──────────────────────────────────────────────────

def _check_rate_limit(request: Request):
    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.allow(client_ip):
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded — try again later",
        )


# ── Routes ─────────────────────────────────────────────────────────────

# ── Health ────────────────────────────────────────────────────────────
# TWO separate checks, because they answer different questions:
#   /health/live  — "is the process alive?"  → instant, NO network calls.
#                   k8s livenessProbe uses this. If it fails the pod restarts.
#   /health/ready — "can it serve traffic?"  → pings DB + Ollama for real.
#                   k8s readinessProbe uses this. 503 = not ready, no traffic.
#   /health       — alias of /health/ready, kept so anything that only reads
#                   the HTTP status code never gets a FAKE 200 when degraded.

async def _ping_database() -> bool:
    """Real DB check: run `SELECT 1` with a hard 3s timeout."""
    try:

        async def _ping() -> None:
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=3.0)
        return True
    except Exception:
        return False


async def _readiness() -> JSONResponse:
    """Probe dependencies and return an HONEST status code."""
    server = get_model_server()
    ollama_ok = await server.health_check()
    database_ok = await _ping_database()
    healthy = ollama_ok and database_ok
    payload = HealthResponse(
        status="healthy" if healthy else "degraded",
        version="0.1.0",
        ollama_reachable=ollama_ok,
        database="connected" if database_ok else "unreachable",
    )
    # Degraded → 503, NOT 200. Monitoring that watches status codes only
    # (load balancers, k8s probes, uptime checks) now sees the truth.
    return JSONResponse(
        status_code=200 if healthy else 503,
        content=payload.model_dump(),
    )


@router.get("/health/live")
async def health_live():
    """Liveness — the process is up. Touches nothing; answers instantly."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready():
    """Readiness — real dependency checks. 200 healthy / 503 degraded."""
    return await _readiness()


@router.get("/health")
async def health():
    """Alias for /health/ready (kept for compatibility; honestly coded)."""
    return await _readiness()


@router.post("/retrieve", dependencies=[Depends(verify_token)])
async def retrieve(
    query: RetrievalQuery,
    request: Request,
    _token: str = Depends(verify_token),
) -> list[RetrievalResult]:
    """Hybrid retrieval: dense + BM25 + RRF + reranking."""
    _check_rate_limit(request)

    cb = get_circuit_breaker("retrieve")
    if not cb.allow():
        raise HTTPException(status_code=503, detail="retrieval service temporarily unavailable")

    retriever = get_retriever()
    try:
        results = await retriever.retrieve(
            query.query,
            top_k=query.top_k,
            use_reranker=query.use_reranker,
            use_rewrite=query.use_rewrite,
            use_multi_hop=query.use_multi_hop,
        )
        cb.record_success()
        return results
    except EmptyCorpusError:
        raise HTTPException(status_code=404, detail="no documents ingested yet")
    except RetrievalError as e:
        cb.record_failure()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await retriever.close()


@router.post("/chat", dependencies=[Depends(verify_token)])
async def chat(
    body: ChatRequest,
    request: Request,
    _token: str = Depends(verify_token),
):
    """RAG chat: retrieve → build prompt → generate (streaming or non-streaming).

    Supports conversation history for multi-turn dialogue.
    """
    _check_rate_limit(request)

    cb = get_circuit_breaker("serve")
    if not cb.allow():
        raise HTTPException(status_code=503, detail="generation service temporarily unavailable")

    retriever = get_retriever()
    server = get_model_server()

    try:
        # Retrieve context
        results = await retriever.retrieve(
            body.query,
            top_k=body.top_k or 5,
            use_reranker=True,
        )

        # Build RAG prompt with conversation history
        context = "\n\n---\n\n".join(r.text for r in results)

        # Build full prompt: system + history + current query
        history_lines: list[str] = []
        for msg in body.history[-10:]:  # Keep last 10 turns for context window
            prefix = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{prefix}: {msg.content}")

        history_block = "\n".join(history_lines) if history_lines else "(no prior messages)"

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- RETRIEVED CONTEXT ---\n"
            f"{context}\n"
            f"--- END CONTEXT ---\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"User: {body.query}\n\n"
            f"Assistant:"
        )

        if body.stream:
            async def event_generator():
                token_iter = await server.generate(
                    prompt,
                    model=body.model,
                    temperature=body.temperature or 0.7,
                    max_tokens=body.max_tokens or 2048,
                    stream=True,
                )
                async for token in token_iter:
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"

            cb.record_success()
            return StreamingResponse(event_generator(), media_type="text/event-stream")

        # Non-streaming
        response_text = await server.generate(
            prompt,
            model=body.model,
            temperature=body.temperature or 0.7,
            max_tokens=body.max_tokens or 2048,
            stream=False,
        )

        cb.record_success()
        return ChatResponse(
            response=response_text,
            sources=[r.model_dump() for r in results],
            model=body.model or "default",
        )

    except ServingError as e:
        cb.record_failure()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        cb.record_failure()
        raise HTTPException(status_code=500, detail=f"chat failed: {e}")
    finally:
        await retriever.close()


# ── Ingest ────────────────────────────────────────────────────────────

@router.post("/ingest", dependencies=[Depends(verify_token)])
async def ingest_file(
    request: Request,
    _token: str = Depends(verify_token),
    file: UploadFile | None = File(default=None),
):
    """Ingest an uploaded file into the vector store.

    Multipart field "file" holds the bytes. The filename's extension selects
    the extractor (pdf/docx/md/html/txt...). The extracted text is chunked,
    embedded, and inserted — so retrieval can actually find it.
    """
    _check_rate_limit(request)

    if file is None:
        # Fallback for the old JSON senders: accept {filename, text}.
        try:
            body = await request.json()
        except Exception:
            body = {}
        text_content = body.get("text", "")
        filename = body.get("filename", "unknown")
        extension = ".md"
    else:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="empty upload")
        filename = file.filename or "upload"
        # Preserve the extension so the extractor picks the right parser.
        extension = Path(filename).suffix.lower() or ".md"
        # Raw bytes → write to a temp file with the same extension.
        text_content = data  # written below

    try:
        from server.ingest import run as run_ingest

        # Stage the upload in a temp dir under its ORIGINAL name so the stored
        # document filename is the user's file name (not a random tmpXXXX) and
        # the extension matches the original for the correct extractor.
        safe_name = Path(filename).name or f"upload{extension}"
        tmp_dir = tempfile.mkdtemp(prefix="vektra-ingest-")
        tmp_path = os.path.join(tmp_dir, safe_name)
        try:
            with open(tmp_path, "wb" if isinstance(text_content, bytes) else "w") as f:
                f.write(text_content)
            report = await run_ingest(
                [tmp_path],
                chunk_strategy="recursive",
                chunk_size=512,
                chunk_overlap=64,
            )
        finally:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)

        if report.errors:
            logger.warning("ingest completed with errors: %s", report.errors)

        return {
            "status": "ok",
            "filename": filename,
            "chunks_created": report.chunks_created,
            "documents_processed": report.documents_processed,
            "errors": report.errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingest failed: %s", e)
        raise HTTPException(status_code=500, detail=f"ingestion failed: {e}")


@router.delete("/ingest/{document_id}", dependencies=[Depends(verify_token)])
async def delete_document(
    document_id: str,
    _token: str = Depends(verify_token),
):
    """Delete a document and all its chunks from the vector store."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            # Delete chunks first
            await session.execute(
                sa_delete(ChunkRow).where(ChunkRow.document_id == document_id)
            )
            # Delete document
            await session.execute(
                sa_delete(DocumentRow).where(DocumentRow.id == document_id)
            )
            await session.commit()

        return {"status": "deleted", "document_id": document_id}

    except Exception as e:
        logger.error("delete failed: %s", e)
        raise HTTPException(status_code=500, detail=f"delete failed: {e}")


@router.post("/benchmark", dependencies=[Depends(verify_token)])
async def benchmark(
    config: BenchmarkRequest,
    request: Request,
    _token: str = Depends(verify_token),
) -> BenchmarkResult:
    """Run model benchmark: TTFT, TPOT, tokens/sec."""
    _check_rate_limit(request)

    server = get_model_server()
    try:
        result = await server.benchmark(config)

        # Write-back to registry
        registry = get_registry()
        try:
            await registry.write_benchmark(result)
        except Exception as e:
            logger.warning("benchmark write-back failed: %s", e)
        finally:
            await registry.close()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"benchmark failed: {e}")


@router.get("/models", dependencies=[Depends(verify_token)])
async def list_models(_token: str = Depends(verify_token)):
    """List registered models."""
    registry = get_registry()
    try:
        models = await registry.list_models()
        return models
    finally:
        await registry.close()


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint.

    generate_latest() returns BYTES (not str). Response accepts bytes directly;
    StreamingResponse would iterate bytes one int at a time and crash.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4",
    )
