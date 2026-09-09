"""SQLAlchemy models for the model registry."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.core.db import Base


class ModelRow(Base):
    """Registered model metadata."""
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    family: Mapped[str | None] = mapped_column(String(64))
    params_count: Mapped[int | None] = mapped_column(Integer)
    quantization: Mapped[str | None] = mapped_column(String(32))
    vram_mb: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="registered")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    versions: Mapped[list["ModelVersionRow"]] = relationship(back_populates="model")
    benchmarks: Mapped[list["BenchmarkResultRow"]] = relationship(back_populates="model")


class ModelVersionRow(Base):
    """Immutable model versions with a `current` pointer."""
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    model: Mapped["ModelRow"] = relationship(back_populates="versions")


class BenchmarkResultRow(Base):
    """Latency profile history from benchmark runs."""
    __tablename__ = "model_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), nullable=False)
    avg_ttft_ms: Mapped[float] = mapped_column(Float)
    avg_tpot_ms: Mapped[float] = mapped_column(Float)
    tokens_per_sec: Mapped[float] = mapped_column(Float)
    total_tokens: Mapped[int] = mapped_column(Integer)
    num_runs: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    model: Mapped["ModelRow"] = relationship(back_populates="benchmarks")
