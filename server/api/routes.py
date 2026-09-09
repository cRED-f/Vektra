"""FastAPI route handlers — /retrieve, /chat, /benchmark, /models, /health, /metrics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from prometheus_client import generate_latest

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

@router.get("/health")
async def health() -> HealthResponse:
    """Health check endpoint."""
    server = get_model_server()
    ollama_ok = await server.health_check()

    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        version="0.1.0",
        ollama_reachable=ollama_ok,
        database="connected",  # TODO: actual DB ping
    )


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
    """RAG chat: retrieve → build prompt → generate (streaming or non-streaming)."""
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

        # Build RAG prompt
        context = "\n\n---\n\n".join(r.text for r in results)
        prompt = (
            f"Answer the user's question based on the following context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {body.query}\n\n"
            f"Answer:"
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
async def metrics():
    """Prometheus metrics endpoint."""
    return StreamingResponse(
        generate_latest(),
        media_type="text/plain",
    )
