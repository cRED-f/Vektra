# Vektra ⚡

[![Next.js](https://img.shields.io/badge/Next.js-16.3.4-black)](https://nextjs.org) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal)](https://fastapi.tiangolo.com) [![PostgreSQL+pgvector](https://img.shields.io/badge/PostgreSQL%2Bpgvector-16-336791)](https://github.com/pgvector/pgvector) [![Ollama](https://img.shields.io/badge/Ollama-qwen2.5%3A1.5b%20%7C%20nomic--embed--text-white)](https://ollama.com)

**Vektra** is a production-oriented **Retrieval-Augmented Generation (RAG)** platform with a **hybrid retrieval** engine, a **model-serving** layer, and a **deep observability** stack — all running on free, open-source infrastructure (pgvector, Ollama, Prometheus, Grafana) behind a Next.js chat interface.

Upload a document (PDF, DOCX, Markdown, HTML, or plain text), and Vektra extracts, chunks, embeds, and indexes it on the fly. Then chat with it: the answer is grounded in your documents via dense + BM25 retrieval, fused with RRF, and re-ranked by a cross-encoder — with the retrieved context fed to a local LLM on Ollama.

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Hybrid retrieval** | Dense (pgvector cosine) **+** BM25 (rank_bm25), fused with **Reciprocal Rank Fusion (RRF)**, then re-ranked by a **cross-encoder** (`cross-encoder/ms-marco-MiniLM-L-6-v2`) |
| **Query rewriting & multi-hop** | Optional query rewriting and query decomposition for complex, multi-part questions |
| **Conversational RAG** | The model is aware of prior chat turns (last 10) via history passed in each request |
| **File upload & inline chunking** | Drag-and-drop / picker upload (PDF, DOCX, DOC, MD, TXT, HTML, HTM, RST), with a live **vertical status bar** showing extract → chunk → embed → insert progress per file |
| **Content-hash idempotency** | Re-uploading the same file is a no-op (dedup by SHA-256) — safe to retry |
| **Streaming chat** | SSE token-by-token responses with time-to-first-token tracking |
| **Dynamic batching** | Non-streaming generation requests are batched by `(model, temperature, max_tokens)` to raise throughput |
| **Circuit breaker & rate limiting** | Retrieval/serving get automatic `503` fail-closed protection; per-IP rate limits (60/min) |
| **Token auth** | Bearer-token auth on all API routes (dev token shipped; change in production) |
| **Observability** | Prometheus metrics + Grafana dashboard: request rate/latency by endpoint, retrieval quality, generation TTFT/TPOT, batch size & queue depth |
| **Model registry** | Model metadata + benchmark results (TTFT, TPOT, tokens/sec) recorded on `/benchmark` |
| **Health probes** | `/health/live` (liveness, instant) and `/health/ready` (readiness, pings DB + Ollama, honest 503 when degraded) |
| **Local & cloud deploy** | Docker Compose for local; Kubernetes manifests (`k8s/`) with HPA + Ingress for a cluster |

---

## 🏗 Architecture

```
                 ┌──────────────────────────────────────────────────┐
                 │                    Frontend                       │
                 │            Next.js 16 + React 19                   │
                 │   landing page · /chat · zustand store             │
                 └──────────────┬───────────────────────────────────┘
                                │  HTTP · Bearer token · SSE stream
                                ▼
                  ┌───────────────────────────────┐
                  │        FastAPI backend        │
                  │          :8000 (uvicorn)      │
                  │  /ingest  /retrieve  /chat    │
                  │  /benchmark  /models  /health │
                  └────┬──────────┬──────────┬────┘
                       │          │          │
        ┌──────────────┴───┐  ┌───▼───────┐  ┌─▼──────────────────┐
        │  Ingestion       │  │ Retrieval │  │  Serving            │
        │  extract→chunk→  │  │ dense +   │  │  Ollama (vLLM opt.) │
        │  embed→insert    │  │ BM25 +    │  │  dynamic batching   │
        │  (pypdf, docx,   │  │ RRF +     │  │  streaming          │
        │   markdownify)   │  │ rerank    │  │                     │
        └────────┬─────────┘  └────┬──────┘  └──────────┬──────────┘
                 │                 │                    │
                 ▼                 ▼                    │   nomic-embed-text
        ┌──────────────────┐  ┌────────────┐            │   qwen2.5:1.5b
        │  PostgreSQL16 +  │  │  BM25 in-  │            │
        │  pgvector        │  │  memory    │            ▼
        │  (chunks+dense   │  │  index     │      ┌────────────┐
        │   embedding)     │  └────────────┘      │   Ollama   │
        └──────────────────┘                      └────────────┘
                                                     host:11434
   /metrics ──► Prometheus(:9091) ──► Grafana(:3001)
```

**Data flow for a question:**
1. **Query** → embedded with `nomic-embed-text`.
2. **Dense search** → top-`k` nearest chunk vectors via pgvector cosine distance.
3. **BM25 search** → top-`k` keyword matches from the in-memory index.
4. **RRF fusion** → merged ranked list (standard `k=60`).
5. **Cross-encoder rerank** → top-k final results.
6. **Prompt** = system prompt + retrieved context + last 10 conversation turns + user query.
7. **Ollama** (`qwen2.5:1.5b`) streams the answer back with each retrieved chunk as a source.

**Data flow for an upload:** extractor (pypdf / python-docx / markdownify / HTMLParser) → recursive or character chunker (512 chars, 64 overlap) → batch embed (`nomic-embed-text`) → upsert document + insert chunks into pgvector, deduped by content SHA-256.

---

## 🧱 Tech Stack

**Backend — Python 3.10+ / FastAPI**
`fastapi` · `uvicorn` · `pydantic` · `pydantic-settings` · `sqlalchemy[asyncio]` · `asyncpg` · `pgvector` · `httpx` · `python-multipart` · `prometheus-client` · `pypdf` · `python-docx` · `markdownify` · `rank-bm25` · `sse-starlette` · `sentence-transformers`

**Frontend — TypeScript / Next.js 16**
`next` 16.3.4 · `react` 19.2.8 · `react-dom` 19.2.8 · `zustand` 5 · `lucide-react` · Tailwind CSS 4 · ESLint 9

**Infrastructure**
PostgreSQL 16 + pgvector · Ollama (`qwen2.5:1.5b` + `nomic-embed-text`) · Docker Compose · Prometheus · Grafana · Kubernetes manifests

---

## 📂 Project Layout

```
├── server/                    # Python backend
│   ├── api/                   # FastAPI layer
│   │   ├── app.py             #   app factory, CORS, request metrics
│   │   ├── routes.py          #   /ingest /retrieve /chat /benchmark /models /health /metrics
│   │   ├── auth.py            #   Bearer-token auth (verify_token)
│   │   ├── circuit_breaker.py #   fail-closed circuit breaker
│   │   └── ratelimit.py       #   per-IP rate limiter
│   ├── ingest/                # ingestion pipeline
│   │   ├── __init__.py        #   run(): extract→chunk→embed→insert
│   │   ├── extractor.py       #   PDF / DOCX / HTML / MD / TXT extractors
│   │   ├── chunker.py         #   character · recursive · markdown strategies
│   │   ├── embedder.py        #   batch embedding via Ollama
│   │   └── inserter.py        #   pgvector upserts (content-hash dedup)
│   ├── retrieve/              # retrieval engine
│   │   ├── retriever.py       #   orchestrates dense + BM25 + RRF + rerank
│   │   ├── dense.py           #   pgvector cosine similarity
│   │   ├── sparse.py          #   BM25 index (rank_bm25)
│   │   ├── fusion.py          #   Reciprocal Rank Fusion
│   │   ├── reranker.py        #   cross-encoder rerank
│   │   └── rewriter.py        #   query rewrite + multi-hop decomposition
│   ├── serve/                 # model serving
│   │   ├── server.py          #   ModelServer (generate / benchmark)
│   │   ├── ollama_backend.py  #   Ollama API adapter
│   │   └── batching.py        #   dynamic request batching
│   ├── registry/              # model registry + benchmark write-back
│   ├── core/                  # config, db, embeddings, schemas, errors, metrics, logging
│   └── main.py                # entry point (uvicorn server.main:app)
│
├── src/                       # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx         #   fonts, metadata, root layout
│   │   ├── page.tsx           #   landing/marketing page
│   │   ├── globals.css        #   design tokens + all component styles
│   │   └── chat/page.tsx      #   the chat app (sidebar, messages, input)
│   ├── components/
│   │   ├── chat/              #   ChatSidebar, ChatInput, FileUploader,
│   │   │                      #   MessageBubble, WelcomeScreen, ChunkingStatusPanel
│   │   ├── Button.tsx         #   landing-page components…
│   │   └── …                  #   HeroInput, NavBar, CodeWindow, QueryBar, Logo…
│   ├── hooks/                 #   useInView, useTypewriter, useTypingPlaceholder
│   └── stores/chat-store.ts   #   zustand store (messages, uploads, queue)
│
├── docker/
│   ├── backend.Dockerfile     #   python:3.12-slim → uvicorn server.main:app
│   ├── frontend.Dockerfile    #   multi-stage Next.js standalone build
│   └── db-init/01-init.sql    #   enables pgvector on first boot
│
├── infra/
│   ├── prometheus/prometheus.yml
│   └── grafana/               #   provisioning + dashboards/vektra.json
│
├── k8s/                       #   cluster deploys (backend, frontend, db, hpa, ingress)
├── scripts/                   #   loadtest.py, sample-knowledge.md
├── docker-compose.yml         #   run the whole stack locally
├── requirements.txt
├── package.json
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** + Docker Compose (`docker compose version` → v2)
- **Ollama** installed locally (backend reaches it via `host.docker.internal:11434`)
  ```bash
  ollama pull qwen2.5:1.5b
  ollama pull nomic-embed-text
  ```

### 1. Run the full stack

```bash
docker compose up -d --build
```

This starts five services:

| Service | Port  | Notes |
|---|---|---|
| `backend` | `8000` | FastAPI (retrieval + chat + ingest) |
| `frontend` | `3000` | Next.js chat UI |
| `db` | `5432` | PostgreSQL 16 + pgvector (`vektra/vektra/vektra`) |
| `prometheus` | `9091` | Metrics scraper (internal `:9090`) |
| `grafana` | `3001` | Dashboards (admin/admin) |

Wait for the backend to be healthy:

```bash
curl -s http://localhost:8000/health
# {"status":"healthy","version":"0.1.0","ollama_reachable":true,"database":"connected","uptime_seconds":0.0}
```

Then open **http://localhost:3000**, click **Chat**, and upload a document.

> Gotcha: if you rebuilt images, Compose keeps old containers because it resolves
> images to worktree-scoped names. Force a recreate:
>
> ```bash
> docker compose build
> docker compose up -d --force-recreate --build
> ```

### 2. Backend only (no frontend)

```bash
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend only (dev)

```bash
npm install        # or: npm ci
npm run dev        # http://localhost:3000
```

---

## 🔐 Configuration

All settings live in `server/core/config.py` (pydantic-settings), overridable via env vars (`VEKTRA_*`) or a `.env` file. Copy `.env.example` → `.env` to get started.

| Variable | Default | Purpose |
|---|---|---|
| `VEKTRA_DATABASE_URL` | `postgresql+asyncpg://vektra:vektra@localhost:5432/vektra` | Postgres + pgvector connection |
| `VEKTRA_AUTO_CREATE_TABLES` | `true` | Create tables on startup (dev; use migrations in prod) |
| `VEKTRA_OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint (set to `http://host.docker.internal:11434` in Docker) |
| `VEKTRA_OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `VEKTRA_OLLAMA_GENERATION_MODEL` | `qwen2.5:1.5b` | Chat generation model |
| `VEKTRA_SERVING_BACKEND` | `ollama` | `ollama` or `vllm` |
| `VEKTRA_BATCH_MAX_SIZE` | `8` | Dynamic batch size cap |
| `VEKTRA_BATCH_MAX_WAIT_MS` | `50` | Max time to wait to fill a batch |
| `VEKTRA_RETRIEVAL_TOP_K` | `20` | Candidates pulled per retriever |
| `VEKTRA_RERANK_TOP_K` | `5` | Final results after reranking |
| `VEKTRA_CROSS_ENCODER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranker model |
| `VEKTRA_API_TOKEN` | `dev-token-change-in-production` | Bearer token for authenticated routes |
| `VEKTRA_GATEWAY_HOST` / `PORT` | `0.0.0.0` / `8000` | Server bind |
| `VEKTRA_RATE_LIMIT_PER_MINUTE` | `60` | Per-IP request budget |
| `VEKTRA_LOG_LEVEL` | `INFO` | Log verbosity |
| `VEKTRA_PROMETHEUS_ENABLED` | `true` | Expose `/metrics` |
| `VEKTRA_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins (JSON list) |
| `VEKTRA_DEBUG` | `false` | Uvicorn reload + debug |

---

## 🔌 API

All routes require a `Authorization: Bearer <VEKTRA_API_TOKEN>` header except `/health*` and `/metrics`. Interactive docs at **http://localhost:8000/docs**.

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness — process up, no deps touched |
| `GET` | `/health/ready` | Readiness — pings DB + Ollama; `503` when degraded |
| `GET` | `/health` | Alias for `/health/ready` |

### Retrieval & Generation
| Method | Path | Description |
|---|---|---|
| `POST` | `/retrieve` | Hybrid retrieve: `{query, top_k, use_reranker, use_rewrite, use_multi_hop}` → ranked chunks with dense/BM25/RRF/rerank scores |
| `POST` | `/chat` | RAG chat: `{query, stream, top_k, model, temperature, max_tokens, history[]}` → SSE stream (`data: <token>` + `data: [DONE]`) or full `{response, sources}` |
| `POST` | `/benchmark` | Run TTFT/TPOT/tokens-per-sec benchmark and write to registry |
| `GET` | `/models` | List registered models |

### Ingestion
| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload a file (multipart field `file`); returns `{status, filename, chunks_created, documents_processed, errors}` |
| `DELETE` | `/ingest/{document_id}` | Delete a document and all its chunks |

### Example — chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What variables did the experimental setup measure?",
    "stream": false,
    "top_k": 5,
    "history": []
  }'
```

### Example — upload
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer dev-token-change-in-production" \
  -F "file=@document.pdf"
```

---

## 📄 `server/api/routes.py` summary

The pipeline is orchestrated in two places:

- **`ingest_file`** (`POST /ingest`) — reads the multipart file, writes it to a temp dir under its **original filename** (so the stored document name and extraction match the user's file), runs `run_ingest(chunk_strategy="recursive", chunk_size=512, chunk_overlap=64)`, and returns the `IngestionReport`. Idempotent via content-hash: a re-upload of identical bytes reports `documents_processed: 0`.
- **`chat`** (`POST /chat`) — retrieves context (`retriever.retrieve` with the reranker on), builds the RAG prompt from a **system prompt** + **retrieved context** + **last 10 conversation turns**, and streams tokens from Ollama.

Two reliability features worth knowing:
- **Circuit breaker** (`server/api/circuit_breaker.py`) — trips after sustained retrieval/serving failures, returning `503` instead of hammering a down dependency.
- **Rate limiter** (`server/api/ratelimit.py`) — per-IP, `VEKTRA_RATE_LIMIT_PER_MINUTE` (60) with a `429` on exceed.

---

## 🖥 Frontend

The chat app (`src/app/chat/page.tsx`) is client-side:

- **Sidebar** (`ChatSidebar.tsx`) — new-chat button, per-session message lists grouped by date, load + delete; persisted to `localStorage`.
- **File upload** (`FileUploader.tsx`) — hidden `<input type="file">` opened via a native `<label htmlFor="vektra-file-input">` (opens the picker with zero JS), off-screen styling so browsers allow it. Validates format + ≤50 MB, builds multipart `FormData`, posts to `/ingest`.
- **Status bar** (`ChunkingStatusPanel.tsx` / inline panel) — live extract / chunk / embed / insert progress with a `%`-filled track and a per-file "done" summary, toggled from the header.
- **Chat input** (`ChatInput.tsx`) — paperclip (upload trigger), auto-growing textarea, Enter-to-send (Shift+Enter for newline), streaming SSE reader that appends tokens to the assistant bubble.
- **State** (`stores/chat-store.ts`, zustand) — messages, recent uploads, upload queue count.

Styling uses CSS custom properties in `globals.css` (ember-orange accent `#ff4d00` across the `--chat-*` tokens), embedded via Tailwind + CSS modules.

---

## 📈 Observability

- **Prometheus** exposes `/metrics` (`prometheus-client`, default registry): request rate/latency by endpoint, retrieval candidate counts, generation TTFT/TPOT/tokens, batch size + queue depth gauges, rerank latency.
- **Grafana** (`infra/grafana/dashboards/vektra.json`) is auto-provisioned against the Prometheus datasource and shows: Requests by endpoint, P95 latency, retrieval quality, generation throughput, and batching behavior.

Dashboards at **http://localhost:3001** (login `admin/admin`).

---

## 🧪 Load testing

`scripts/loadtest.py` fires `--concurrency` requests and reports latency percentiles, throughput, and error rate:

```bash
# against the docker-compose backend
python scripts/loadtest.py

# 200 requests against the search endpoint
python scripts/loadtest.py --url http://localhost:8000 --requests 200 \
  --endpoint /retrieve --method POST --token dev-token-change-in-production
```

---

## ☸ Kubernetes

`k8s/` holds cluster manifests: `db.yaml` (pgvector), `backend-deployment.yaml` + `backend-service.yaml`, `frontend.yaml`, `hpa.yaml` (HorizontalPodAutoscaler), `ingress.yaml`. The backend uses `/healthz`-style probes (`/health/live` liveness via `k8s` dashboard). Port-forward for local testing:

```bash
kubectl port-forward svc/backend 18000:8000
python scripts/loadtest.py --url http://localhost:18000 --requests 200
```

---

## 🔒 Security notes

- The default `VEKTRA_API_TOKEN` (`dev-token-change-in-production`) is insecure — **change it before any real deployment**.
- Token auth uses HTTP Bearer (not HTTPS by default). Terminate TLS at the ingress in production.
- CORS is locked to the frontend origin by default.
- The default Postgres/DB and Grafana credentials are development defaults — change them for shared environments.

---

## 🧭 Roadmap / possible next steps

- [ ] Alembic migrations instead of auto-create on startup
- [ ] Ingestion job queue + chunking observability panel persistence
- [ ] vLLM backend toggle end-to-end (config exists, `VEKTRA_SERVING_BACKEND=vllm`)
- [ ] More chunking strategies / configurable size & overlap via the UI
- [ ] Multi-user auth + per-user corpora
- [ ] Unit + integration test suite wired into CI

---

## 📄 License & Credits

ME — you decide. (Add your license here before publishing.) Stack: [FastAPI](https://fastapi.tiangolo.com), [Next.js](https://nextjs.org), [pgvector](https://github.com/pgvector/pgvector), [Ollama](https://ollama.com), [Prometheus](https://prometheus.io), [Grafana](https://grafana.com).

Built for **free, open-source RAG on measured latency** — no paid inference.