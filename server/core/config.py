"""Single source of truth for all Vektra configuration.

Uses pydantic-settings to load from environment / .env files.
Every other module imports Settings from here — never reads os.environ directly.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Vektra backend configuration.

    Load order: env vars > .env file > defaults below.
    """

    model_config = SettingsConfigDict(
        env_prefix="VEKTRA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://vektra:vektra@localhost:5432/vektra"
    database_echo: bool = False
    # Dev convenience — create tables on startup. Use Alembic/migrations in prod.
    auto_create_tables: bool = True

    # ── Ollama ────────────────────────────────────────────────────────
    ollama_host: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_generation_model: str = "qwen2.5:1.5b"

    # ── Serving ───────────────────────────────────────────────────────
    serving_backend: str = "ollama"  # "ollama" | "vllm"
    vllm_host: str = "http://localhost:8080"
    batch_max_size: int = 8
    batch_max_wait_ms: float = 50.0

    # ── Retrieval ─────────────────────────────────────────────────────
    retrieval_top_k: int = 20
    rerank_top_k: int = 5
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Auth ──────────────────────────────────────────────────────────
    api_token: str = "dev-token-change-in-production"

    # ── Gateway ───────────────────────────────────────────────────────
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000
    rate_limit_per_minute: int = 60

    # ── Observability ─────────────────────────────────────────────────
    log_level: str = "INFO"
    prometheus_enabled: bool = True

    # ── Frontend (for CORS / proxy) ───────────────────────────────────
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── Debug ──────────────────────────────────────────────────────────
    debug: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call get_settings() everywhere."""
    return Settings()
