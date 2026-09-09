"""RegistryClient — CRUD for model registry + benchmark write-back."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_session_factory
from server.core.errors import ModelNotFoundError
from server.core.logging import get_logger
from server.core.schemas import BenchmarkResult, ModelInfo
from server.registry.models import BenchmarkResultRow, ModelRow, ModelVersionRow

logger = get_logger("registry.client")


class RegistryClient:
    """Library interface for model registry CRUD."""

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            factory = get_session_factory()
            self._session = factory()
            self._own_session = True
        return self._session

    # ── Model CRUD ──────────────────────────────────────────────────────

    async def register(
        self,
        model_id: str,
        name: str,
        *,
        family: str | None = None,
        params_count: int | None = None,
        quantization: str | None = None,
        vram_mb: int | None = None,
        version: str = "1.0.0",
        artifact_path: str | None = None,
    ) -> ModelInfo:
        """Register a new model with an initial version."""
        session = await self._get_session()
        model = ModelRow(
            id=model_id,
            name=name,
            family=family,
            params_count=params_count,
            quantization=quantization,
            vram_mb=vram_mb,
            status="registered",
        )
        session.add(model)

        ver = ModelVersionRow(
            model_id=model_id,
            version=version,
            artifact_path=artifact_path,
            is_current=True,
        )
        session.add(ver)
        await session.commit()
        logger.info("registered model %s (v%s)", model_id, version)

        return await self.get(model_id)

    async def get(self, model_id: str) -> ModelInfo:
        """Get model info by ID."""
        session = await self._get_session()
        result = await session.execute(
            select(ModelRow).where(ModelRow.id == model_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ModelNotFoundError(f"model {model_id} not found")

        # Get current version
        ver_result = await session.execute(
            select(ModelVersionRow).where(
                ModelVersionRow.model_id == model_id,
                ModelVersionRow.is_current == True,
            )
        )
        ver = ver_result.scalar_one_or_none()

        # Get latest benchmark
        bench_result = await session.execute(
            select(BenchmarkResultRow)
            .where(BenchmarkResultRow.model_id == model_id)
            .order_by(BenchmarkResultRow.created_at.desc())
            .limit(1)
        )
        bench = bench_result.scalar_one_or_none()

        return ModelInfo(
            model_id=row.id,
            name=row.name,
            family=row.family,
            params_count=row.params_count,
            quantization=row.quantization,
            vram_mb=row.vram_mb,
            status=row.status,
            current_version=ver.version if ver else None,
            avg_ttft_ms=bench.avg_ttft_ms if bench else None,
            avg_tpot_ms=bench.avg_tpot_ms if bench else None,
            tokens_per_sec=bench.tokens_per_sec if bench else None,
        )

    async def list_models(self) -> list[ModelInfo]:
        """List all registered models."""
        session = await self._get_session()
        result = await session.execute(select(ModelRow))
        rows = result.scalars().all()
        models = []
        for row in rows:
            try:
                models.append(await self.get(row.id))
            except Exception as e:
                logger.warning("failed to load model %s: %s", row.id, e)
        return models

    async def update_status(self, model_id: str, status: str):
        """Update model status (e.g. 'loaded', 'error')."""
        session = await self._get_session()
        await session.execute(
            update(ModelRow).where(ModelRow.id == model_id).values(status=status)
        )
        await session.commit()
        logger.info("model %s status -> %s", model_id, status)

    # ── Version management ──────────────────────────────────────────────

    async def add_version(
        self,
        model_id: str,
        version: str,
        artifact_path: str | None = None,
        set_current: bool = True,
    ):
        """Add a new version. Optionally set as current."""
        session = await self._get_session()

        if set_current:
            # Clear current flag
            await session.execute(
                update(ModelVersionRow).where(
                    ModelVersionRow.model_id == model_id,
                    ModelVersionRow.is_current == True,
                ).values(is_current=False)
            )

        ver = ModelVersionRow(
            model_id=model_id,
            version=version,
            artifact_path=artifact_path,
            is_current=set_current,
        )
        session.add(ver)
        await session.commit()
        logger.info("added version %s for model %s", version, model_id)

    # ── Benchmark write-back ────────────────────────────────────────────

    async def write_benchmark(self, result: BenchmarkResult):
        """Write a benchmark result to the latency profile history."""
        session = await self._get_session()
        row = BenchmarkResultRow(
            model_id=result.model,
            avg_ttft_ms=result.avg_ttft_ms,
            avg_tpot_ms=result.avg_tpot_ms,
            tokens_per_sec=result.tokens_per_sec,
            total_tokens=result.total_tokens,
            num_runs=result.num_runs,
        )
        session.add(row)
        await session.commit()
        logger.info(
            "benchmark written for %s: %.1f tok/s, TTFT %.1fms",
            result.model, result.tokens_per_sec, result.avg_ttft_ms,
        )

    async def close(self):
        if self._own_session and self._session:
            await self._session.close()
