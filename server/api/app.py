"""FastAPI application factory."""

from __future__ import annotations

import time

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes import router
from server.core.config import get_settings
from server.core.db import init_db
from server.core.logging import get_logger, setup_logging
from server.core.metrics import request_latency_seconds, request_total

logger = get_logger("api.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    setup_logging()
    settings = get_settings()
    if settings.auto_create_tables:
        await init_db()
    yield


async def _record_request_metrics(request: Request, call_next):
    """Middleware: record gateway request count + latency per route.

    This is what powers the Grafana panels — without it the dashboard stays flat.
    `request.scope["route"].path` gives the route TEMPLATE (e.g. "/health"),
    so distinct hits to the same endpoint group together.
    """
    method = request.method
    start = time.monotonic()

    response = await call_next(request)
    # Routing happens INSIDE call_next, so the route template is only known
    # after it returns. Read it post-call or it's "unknown".
    route = request.scope.get("route")
    endpoint = route.path if route else "unknown"
    status = response.status_code
    latency = time.monotonic() - start
    request_total.labels(method=method, endpoint=endpoint, status=status).inc()
    request_latency_seconds.labels(method=method, endpoint=endpoint).observe(latency)

    return response


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Vektra API",
        version="0.1.0",
        description="RAG + Model Serving Platform",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gateway request metrics (added AFTER CORS so CORS runs outermost).
    # The outermost middleware wraps the innermost request.
    app.middleware("http")(_record_request_metrics)

    # Routes
    app.include_router(router)

    return app
