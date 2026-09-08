"""SQLAlchemy async engine + pgvector table definitions.

Uses asyncpg driver for PostgreSQL. Tables are created via metadata.create_all
(or Alembic migrations in production). pgvector columns use the Vector type
from pgvector.sqlalchemy.
"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from server.core.config import get_settings


# ── Base ──────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── Models ────────────────────────────────────────────────────────────


class DocumentRow(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, unique=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class ChunkRow(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False, index=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # nomic-embed-text produces 768-dim vectors
    chunk_index = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class ModelRow(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    family = Column(String, default="")
    params = Column(String, default="")
    quantization = Column(String, default="")
    vram_mb = Column(Integer, default=0)
    status = Column(String, default="unloaded")
    latency_profile = Column(Text, default="{}")
    created_at = Column(DateTime, server_default=func.now())


# ── Engine / Session ─────────────────────────────────────────────────


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields an async session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session  # type: ignore[misc]


async def init_db():
    """Create all tables (dev convenience — use Alembic in prod)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
