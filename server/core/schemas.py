"""Canonical Pydantic models — single source of truth for the API contract.

These double as the OpenAPI schema (FastAPI reads them directly) and as the
basis for the frontend's TypeScript types (generate from the OpenAPI JSON).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────


class ChunkStrategy(str, Enum):
    """Supported chunking strategies."""

    CHARACTER = "character"
    RECURSIVE = "recursive"
    MARKDOWN = "markdown"


class ModelStatus(str, Enum):
    """Model lifecycle status."""

    LIVE = "live"
    LOADING = "loading"
    ERROR = "error"
    UNLOADED = "unloaded"


# ── Ingestion ─────────────────────────────────────────────────────────


class Document(BaseModel):
    """An ingested document (source file metadata)."""

    id: str = Field(description="Deterministic ID (content hash)")
    filename: str
    content_hash: str = Field(description="SHA-256 of raw content for dedup")
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    """A single chunk with embedding — the core unit stored in pgvector."""

    id: str = Field(description="Deterministic ID (hash of content)")
    document_id: str
    text: str
    embedding: list[float] = Field(default_factory=list)
    chunk_index: int = 0
    token_count: int = 0
    metadata: dict = Field(default_factory=dict)


class IngestionReport(BaseModel):
    """Result of an ingestion run."""

    documents_processed: int = 0
    chunks_created: int = 0
    chunks_skipped: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


# ── Retrieval ─────────────────────────────────────────────────────────


class RetrievalQuery(BaseModel):
    """A retrieval request."""

    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    use_reranker: bool = True
    use_rewrite: bool = False


class RetrievalResult(BaseModel):
    """A single retrieved chunk with scores."""

    chunk_id: str
    document_id: str
    text: str
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    rank: int = 0


# ── Chat / Generation ────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Chat request — retrieve + generate."""

    query: str = Field(min_length=1, max_length=4000)
    stream: bool = True
    top_k: int = Field(default=5, ge=1, le=20)
    model: str | None = Field(default=None, description="Override generation model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class ChatDelta(BaseModel):
    """A single streamed token delta."""

    delta: str
    finish_reason: str | None = None


class ChatResponse(BaseModel):
    """Non-streaming chat response."""

    answer: str
    sources: list[RetrievalResult] = Field(default_factory=list)
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0


# ── Benchmark ─────────────────────────────────────────────────────────


class BenchmarkRequest(BaseModel):
    """Benchmark configuration."""

    prompt: str = "Explain what retrieval-augmented generation is."
    model: str | None = None
    max_tokens: int = 256
    num_iterations: int = 5


class BenchmarkResult(BaseModel):
    """Latency / throughput measurements for a model."""

    model: str
    ttft_ms: float = Field(description="Time to first token (ms)")
    tpot_ms: float = Field(description="Time per output token (ms)")
    tokens_per_sec: float = 0.0
    total_tokens: int = 0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    iterations: int = 0
    errors: int = 0


# ── Model Registry ───────────────────────────────────────────────────


class ModelInfo(BaseModel):
    """Registered model metadata."""

    id: str
    name: str
    family: str = ""
    params: str = ""
    quantization: str = ""
    vram_mb: int = 0
    status: ModelStatus = ModelStatus.UNLOADED
    latency_profile: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelLoad(BaseModel):
    """Request to load/unload a model."""

    model_id: str
    backend: str = "ollama"


# ── Health ────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Gateway health check."""

    status: str = "ok"
    version: str = "0.1.0"
    database: str = "ok"
    ollama: str = "ok"
    uptime_seconds: float = 0.0
