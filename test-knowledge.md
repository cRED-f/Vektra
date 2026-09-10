# Vektra Chat Bot Test Knowledge Base

This document can be used to test the Vektra chat bot with some predefined content.

## What is Vektra?

Vektra is a production retrieval and model serving platform that provides hybrid RAG (Retrieval-Augmented Generation) capabilities. It combines:

1. **Ingestion Pipeline**: Extract content from PDF, DOCX, HTML, MD, TXT files
2. **Dense Retrieval**: Vector-based semantic search using pgvector
3. **Sparse Retrieval**: BM25 keyword-based search
4. **Fusion**: RRF (Reciprocal Rank Fusion) to combine dense and sparse results
5. **Reranking**: Cross-encoder re-ranking for precision
6. **Model Serving**: Dynamic batching with Ollama for fast generation

## Key Features

- **Hybrid Search**: Combines semantic and keyword search for accurate results
- **Context-Aware**: Answers questions based on ingested documentation
- **Streaming Responses**: Real-time token streaming for instant feedback
- **Metrics & Observability**: Prometheus + Grafana for production monitoring
- **Docker Orchestration**: Easy deployment with Docker Compose

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, pgvector
- **Frontend**: Next.js 16, React 19, Tailwind CSS v4
- **ML Models**: Ollama (nomic-embed-text, qwen2.5:1.5b)
- **Database**: PostgreSQL with pgvector extension
- **Infrastructure**: Docker, Prometheus, Grafana, Kubernetes

## How It Works

1. **Ingest Documents**: Use the CLI to load documentation into the system
2. **User Asks Question**: Frontend sends query to backend API
3. **Retrieve Context**: Backend searches ingested chunks, ranks results
4. **Generate Answer**: Backend builds RAG prompt, generates response with streaming
5. **Display Result**: Frontend shows answer in real-time