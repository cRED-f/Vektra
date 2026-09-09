"""Prometheus counter/histogram helpers.

Every public entry point imports these helpers to emit metrics.
Metric names are defined here once so dashboards stay stable.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info

# ── Info ──────────────────────────────────────────────────────────────

app_info = Info("vektra", "Vektra application info")

# ── Ingestion ─────────────────────────────────────────────────────────

ingest_documents_total = Counter(
    "vektra_ingest_documents_total",
    "Documents processed",
    ["status"],  # success | error | skipped
)

ingest_chunks_total = Counter(
    "vektra_ingest_chunks_total",
    "Chunks created during ingestion",
)

# ── Retrieval ─────────────────────────────────────────────────────────

retrieve_latency_seconds = Histogram(
    "vektra_retrieve_latency_seconds",
    "Retrieval pipeline latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

retrieve_candidates_total = Histogram(
    "vektra_retrieve_candidates_total",
    "Number of candidates before reranking",
    buckets=[5, 10, 25, 50, 100],
)

rerank_latency_seconds = Histogram(
    "vektra_rerank_latency_seconds",
    "Cross-encoder rerank latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# ── Generation / Serving ──────────────────────────────────────────────

generate_latency_seconds = Histogram(
    "vektra_generate_latency_seconds",
    "End-to-end generation latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

generate_ttft_seconds = Histogram(
    "vektra_generate_ttft_seconds",
    "Time to first token",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

generate_tokens_total = Counter(
    "vektra_generate_tokens_total",
    "Tokens generated",
    ["type"],  # prompt | completion
)

batch_size = Histogram(
    "vektra_batch_size",
    "Dynamic batch sizes",
    buckets=[1, 2, 4, 8, 16, 32],
)

queue_depth = Gauge(
    "vektra_queue_depth",
    "Request queue depth at batching",
)

# ── Gateway ───────────────────────────────────────────────────────────

request_total = Counter(
    "vektra_request_total",
    "Total gateway requests",
    ["method", "endpoint", "status"],
)

request_latency_seconds = Histogram(
    "vektra_request_latency_seconds",
    "Gateway request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# ── Errors ────────────────────────────────────────────────────────────

errors_total = Counter(
    "vektra_errors_total",
    "Domain errors",
    ["code"],  # retrieval_error | serving_error | auth_error | ...
)
