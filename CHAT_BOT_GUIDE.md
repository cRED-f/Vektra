# 🤖 Vektra Chat Bot User Guide

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services including database and Ollama
docker-compose up -d

# Build and run containers
docker-compose up -d

# Wait for services to be ready (Database starts first)
# Check logs with: docker-compose logs -f
```

Access the chat interface at: **http://localhost:3000/chat**

### Option 2: Manual Startup

```bash
# 1. Start database and Ollama
# (Handled by docker-compose.yml)

# 2. Ingest test data (optional)
docker exec -it vektra-backend python -m server.ingest.cli ./test-knowledge.md

# 3. Build containers (already done)
docker build -f docker/backend.Dockerfile -t vektra-backend:latest .
docker build -f docker/frontend.Dockerfile -t vektra-frontend:latest .

# 4. Start containers
docker run -d --name vektra-backend -p 8000:8000 --env-file .env vektra-backend:latest
docker run -d --name vektra-frontend -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://host.docker.internal:8000 vektra-frontend:latest
```

## 📝 Ingesting Your Own Documents

### Using the CLI

```bash
docker exec -it vektra-backend python -m server.ingest.cli \
  ./path/to/your/document.pdf \
  ./path/to/your/document.docx \
  ./path/to/directory/*
```

### Command-Line Options

```bash
python -m server.ingest.cli <paths> [options]

Options:
  --strategy {character,recursive,markdown}
      Chunking strategy (default: recursive)

  --chunk-size <int>
      Target chunk size in characters (default: 512)

  --chunk-overlap <int>
      Overlap between chunks (default: 64)
```

Supported formats: **PDF, DOCX, HTML, MD, TXT, RST**

### Online Production Ingestion

```bash
VEKTRA_OLLAMA_HOST=http://localhost:11434 \
VEKTRA_DATABASE_URL=postgresql+asyncpg://vektra:vektra@localhost:5432/vektra \
python -m server.ingest.cli ./my-doc.pdf ./my-report.docx
```

---

## 🎯 Using the Chat Bot

### Basic Chat

1. Open **http://localhost:3000/chat**
2. Type your question in the input field
3. Press **Enter** (Shift+Enter for new line)
4. Watch the response stream in real-time

### Example Queries

```typescript
// Questions the chat bot can answer:
"What is Vektra?"
"What are the key features of the RAG pipeline?"
"How does hybrid search work in Vektra?"
"What databases does Vektra use?"
"What tech stack is used for the frontend?"

// Multi-hop queries (if enabled):
"Why would you choose heavy partitioning for distributed OLAP workloads?"
"Explain how FastAPI handles asynchronous operations with asyncio."
```

### Advanced Features

**Streaming Responses**
- Tokens appear character-by-character
- Cursor animation shows typing in progress
- Auto-scrolls to latest content

**Source Attribution**
- Retrieved chunks displayed with scores
- Shows dense, BM25, RRF, and rerank scores
- Helps verify answer accuracy

**Context Window**
- Maximum 5 chunks returned (customizable)
- Refined from 20 candidates using reranking
- Fusion of dense + sparse retrieval

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database (PostgreSQL + pgvector)
VEKTRA_DATABASE_URL=postgresql+asyncpg://vektra:vektra@localhost:5432/vektra
VEKTRA_AUTO_CREATE_TABLES=true

# Ollama
VEKTRA_OLLAMA_HOST=http://localhost:11434
VEKTRA_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
VEKTRA_OLLAMA_GENERATION_MODEL=qwen2.5:1.5b

# Retrieval
VEKTRA_RETRIEVAL_TOP_K=20           # Candidates to fetch
VEKTRA_RERANK_TOP_K=5               # Final results (default)
VEKTRA_CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Auth (Development mode)
VEKTRA_API_TOKEN=dev                    # Change for production

# Gateway
VEKTRA_GATEWAY_HOST=0.0.0.0
VEKTRA_GATEWAY_PORT=8000
VEKTRA_RATE_LIMIT_PER_MINUTE=60

# Cors (Frontend URL)
VEKTRA_CORS_ORIGINS=["http://localhost:3000"]
```

### Production Deployment

```bash
# Change these in .env
VEKTRA_API_TOKEN=your-strong-random-token-here
VEKTRA_DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/vektra
VEKTRA_OLLAMA_HOST=https://ollama.your-domain.com
VEKTRA_CORS_ORIGINS=["https://your-domain.com"]
```

---

## 📊 API Reference

### POST /chat

Stream a chat response with RAG.

**Headers**:
```
Content-Type: application/json
Authorization: Bearer $VEKTRA_API_TOKEN
```

**Body**:
```json
{
  "query": "Your question here...",
  "stream": true,
  "top_k": 5,
  "model": "qwen2.5:1.5b",        // Optional
  "temperature": 0.7,               // Optional (0-2)
  "max_tokens": 2048                // Optional (1-8192)
}
```

**Response** (SSE Stream):
```
[DONE]
```

**Non-Streaming**:
```json
{
  "response": "Answer here...",
  "sources": [...],
  "model": "qwen2.5:1.5b",
  "tokens_used": 150,
  "latency_ms": 1234.56
}
```

### GET /health/ready

Check if backend is operational.

**Response**:
```json
{
  "status": "healthy" | "degraded",
  "version": "0.1.0",
  "ollama_reachable": true,
  "database": "connected"
}
```

### POST /retrieve

Test retrieval only (no generation).

**Headers**:
```
Authorization: Bearer $VEKTRA_API_TOKEN
```

**Body**:
```json
{
  "query": "test query",
  "top_k": 5,
  "use_reranker": true,
  "use_rewrite": false,
  "use_multi_hop": false
}
```

**Response**:
```json
[
  {
    "chunk_id": "abc123",
    "document_id": "doc-xyz",
    "text": "Retrieved content...",
    "dense_score": 0.850,
    "bm25_score": 750.2,
    "rrf_score": 0.890,
    "rerank_score": 0.925,
    "rank": 1
  }
]
```

---

## 🐛 Troubleshooting

### "Empty response from chat"

**Cause**: No documents ingested.

**Solution**:
```bash
docker exec -it vektra-backend python -m server.ingest.cli ./test-knowledge.md
```

### "Invalid token" error

**Cause**: Auth token mismatch.

**Solution**: Check `.env` has `VEKTRA_API_TOKEN=dev` or update [src/app/chat/page.tsx](src/app/chat/page.tsx:10).

### "No documents ingested yet"

**Cause**: Empty database.

**Solution**: Run ingestion pipeline first.

### "Ollama not reachable"

**Cause**: Ollama not running.

**Solution**: Start Ollama with `ollama serve` or ensure Docker Compose is running.

### Slow responses (5+ seconds)

**Cause**: Database latency or small BM25 index.

**Solutions**:
- Use `--strategy recursive` with larger chunks
- Monitor retrieval with Prometheus metrics
- Check database connection quality

---

## 📈 Monitoring & Observability

### Prometheus Metrics

```
GET http://localhost:8000/metrics
```

Key metrics:
- `request_total` - Number of API requests
- `request_latency_seconds` - Per-route latency
- `generate_latency_seconds` - Generation time
- `generate_ttft_seconds` - Time to first token
- `generate_tokens_total` - Tokens generated

### Grafana Dashboards

Access Grafana at: **http://localhost:3001**

Default credentials:
- Username: `admin`
- Password: `admin`

---

## 🔐 Security Checklist

- [ ] Change `VEKTRA_API_TOKEN` from `dev`
- [ ] Update `VEKTRA_CORS_ORIGINS` for production URL
- [ ] Secure PostgreSQL database (strong password)
- [ ] Protect Ollama endpoint (IP whitelist or HTTPS)
- [ ] Enable rate limiting (`VEKTRA_RATE_LIMIT_PER_MINUTE`)
- [ ] Use production-grade embedding model (not nomic-embed-text)
- [ ] Monitor metrics and logs
- [ ] Implement CORS properly

---

## 📞 Support

**Documentation**:
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Technical details
- [DESIGN.md](DESIGN.md) - Design system reference

**Logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## 🎉 Success State

When everything is working, you should see:

1. ✅ **Database** running with pgvector extension
2. ✅ **Ollama** responding at `http://localhost:11434`
3. ✅ **Backend** listening on `port 8000`
4. ✅ **Frontend** accessible at `http://localhost:3000/chat`
5. ✅ **Chat bot** responding with streaming text
6. ✅ **Metrics** flowing to Prometheus/Grafana

Happy chatting! 🚀