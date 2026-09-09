# Vektra Platform Overview

Vektra is a production RAG (Retrieval-Augmented Generation) and model serving
platform. It combines hybrid retrieval with a pluggable inference backend.

## Architecture

The platform is split into four main components. The ingestion pipeline
extracts text from documents, splits it into chunks, embeds each chunk into a
768-dimensional vector using the nomic-embed-text model, and inserts the
vectors into a PostgreSQL database with the pgvector extension.

The retrieval service performs hybrid search: dense vector search combined
with BM25 keyword search, merged with Reciprocal Rank Fusion (RRF). Results
can be re-ranked with a cross-encoder before being returned.

The serving layer connects to Ollama for both embeddings and text generation.
Generation uses the qwen2.5:1.5b model. The gateway exposes REST endpoints for
retrieval and chat, with rate limiting, a circuit breaker, and authentication.

## Observability

The gateway exposes Prometheus metrics for request latency and throughput.
Grafana provides dashboards built from those metrics. The whole stack can be
deployed with Docker Compose, Kubernetes, or Terraform.

## Deployment

Locally the stack runs with docker compose. For production, Kubernetes
Deployments scale the backend horizontally with a HorizontalPodAutoscaler, and
Terraform provisions cloud infrastructure as code.
