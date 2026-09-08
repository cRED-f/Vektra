"""Domain exception hierarchy.

Every module raises these. The API layer (M5) catches them and maps
to HTTP responses. Never return error strings — raise these instead.
"""

from __future__ import annotations


class VektraError(Exception):
    """Base for all Vektra domain errors."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str = "", details: dict | None = None):
        self.message = message or self.__class__.__doc__ or self.code
        self.details = details or {}
        super().__init__(self.message)


# ── Ingestion ─────────────────────────────────────────────────────────


class IngestionError(VektraError):
    """Ingestion pipeline failed."""

    code = "ingestion_error"
    status_code = 500


class DuplicateDocumentError(IngestionError):
    """Document already ingested (content hash match)."""

    code = "duplicate_document"
    status_code = 409


# ── Retrieval ─────────────────────────────────────────────────────────


class RetrievalError(VektraError):
    """Retrieval pipeline failed."""

    code = "retrieval_error"
    status_code = 500


class EmptyCorpusError(RetrievalError):
    """No documents have been ingested yet."""

    code = "empty_corpus"
    status_code = 404


# ── Serving ───────────────────────────────────────────────────────────


class ServingError(VektraError):
    """Model serving failed."""

    code = "serving_error"
    status_code = 500


class ModelNotFoundError(ServingError):
    """Requested model is not available."""

    code = "model_not_found"
    status_code = 404


class ModelLoadError(ServingError):
    """Failed to load a model into memory."""

    code = "model_load_error"
    status_code = 500


# ── Auth ──────────────────────────────────────────────────────────────


class AuthError(VektraError):
    """Authentication failed."""

    code = "auth_error"
    status_code = 401


class RateLimitError(VektraError):
    """Rate limit exceeded."""

    code = "rate_limit_exceeded"
    status_code = 429
