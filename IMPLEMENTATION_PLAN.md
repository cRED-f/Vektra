# Chat Bot Implementation Plan

## 📋 Overview
Implement end-to-end chat bot functionality with RAG (Retrieval-Augmented Generation).

## ✅ Current Status
- Backend APIs are complete ([routes.py](server/api/routes.py:163))
- Frontend UI is complete ([page.tsx](src/app/chat/page.tsx))
- Docker images built (backend: 9.66GB)
- `.env` file created

## 🔧 Implementation Steps

### Step 1: Fix Authentication Header
**Issue**: Frontend doesn't send API token.

**Action**:
- Update `src/app/chat/page.tsx` to include auth header
- Set `Authorization: Bearer dev` (dev mode)

### Step 2: Populate Test Data
**Action**:
- Create test documents for ingestion
- Use `python -m server.ingest.cli` to load them into database

### Step 3: Verify Ollama Setup
**Check**:
- Ollama is running (http://localhost:11434)
- Models installed: `nomic-embed-text`, `qwen2.5:1.5b`

### Step 4: Build Frontend Docker Image
**Action**:
```bash
docker build -f docker/frontend.Dockerfile -t vektra-frontend:latest .
```

### Step 5: Start Docker Services
**Command**:
```bash
docker-compose up -d
```

### Step 6: Test Chat Endpoint
**Test**:
- Visit http://localhost:3000/chat
- Send a query (e.g., "What is Vektra?")
- Verify streaming response works

## 🎯 Chat Bot Logic Flow

```
┌─────────────┐
│   User      │
│  Message    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Frontend (localhost:3000/chat)                 │
│  - Accept user input                            │
│  - Forward to backend                           │
│  - Stream display results                       │
└───────────┬─────────────────────────────────────┘
            │ POST /chat
            │ Headers: Authorization: Bearer {token}
            │ Body: {query, stream: true, top_k: 5}
            ▼
┌─────────────────────────────────────────────────┐
│  Backend API (localhost:8000)                    │
│  1. Verify token (auth.py)                      │
│  2. Retrieve chunks (retriever.py)              │
│     - Dense search + BM25                      │
│     - RRF fusion                               │
│     - Cross-encoder rerank                      │
│  3. Build prompt                                │
│  4. Generate response (ollama_backend.py)       │
│     - Stream tokens one-by-one                 │
│     - Track TTFT, tokens/sec                   │
└───────────┬─────────────────────────────────────┘
            │ SSE Stream ({token})
            ▼
┌─────────────────────────────────────────────────┐
│  Frontend Display                                │
│  - Show user message                            │
│  - Display assistant message with cursor       │
│  - Auto-scroll to bottom                        │
└─────────────────────────────────────────────────┘
```

## 📊 RAG Pipeline Details

### Retrieval Phase
1. **Query Embedding**: `nomic-embed-text` converts user query to vector
2. **Dense Search**: Cosine similarity in pgvector
3. **BM25 Search**: Keyword-based retrieval
4. **RRF Fusion**: Reciprocal Rank Fusion (k=60)
5. **Reranking**: Cross-encoder re-ranks top 50 results
6. **Return**: Top 5 chunks with scores

### Generation Phase
1. **Prompt Construction**:
   ```
   Answer the user's question based on the following context.

   Context:
   {chunk1}\n\n{chunk2}\n\n{chunk3}...

   Question: {user_query}
   Answer:
   ```

2. **Streaming Generation**:
   - Ollama streams token-by-token
   - Each token forwarded to frontend
   - Frontend concatenates and renders

3. **Metrics Tracked**:
   - TTFT (Time to First Token)
   - Tokens per second
   - Total tokens generated
   - Retrieval latency

## 🔐 Security Note

- **Development**: Using `dev` token (no actual authentication)
- **Production**: MUST change `VEKTRA_API_TOKEN` in `.env`
- **CORS**: Only allows localhost:3000 (user should update in .env)
- **Rate Limiting**: 60 requests per minute (configurable)

## 🚀 Quick Start

```bash
# 1. Make sure Docker is running
docker-compose up -d

# 2. Optional: Populate test data
docker exec -it vektra-backend python -m server.ingest.cli /path/to/documents

# 3. Build frontend
docker build -f docker/frontend.Dockerfile -t vektra-frontend:latest .

# 4. Run frontend
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://backend:8000 vektra-frontend:latest

# 5. Test chat
# Visit http://localhost:3000/chat
```

## 🐛 Troubleshooting

**Issue**: "No documents ingested yet"
- **Fix**: Run ingestion pipeline first

**Issue**: "Invalid token"
- **Fix**: Check `.env` has `VEKTRA_API_TOKEN=dev` or update frontend header

**Issue**: "Ollama not reachable"
- **Fix**: Start Ollama: `ollama serve` or use `docker compose up -d` (includes Ollama)

**Issue**: "Empty response"
- **Fix**: Check database has chunks, verify embeddings exist