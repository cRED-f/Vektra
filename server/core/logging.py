"""Structured logging setup.

Use get_logger() everywhere. Logs are JSON in production, human-readable
in development. Correlation IDs are injected via contextvars.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

from server.core.config import get_settings

# ── Correlation ID ────────────────────────────────────────────────────

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


# ── Formatter ─────────────────────────────────────────────────────────


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter — no external deps."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        rid = request_id_ctx.get()
        prefix = f"{color}{record.levelname:8s}{self.RESET} [{rid}]"
        msg = f"{prefix} {record.name}: {record.getMessage()}"
        if record.exc_info and record.exc_info[0] is not None:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


# ── Setup ─────────────────────────────────────────────────────────────


def setup_logging():
    """Configure root logger once at startup."""
    settings = get_settings()
    root = logging.getLogger("vektra")
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_level.upper() == "DEBUG":
        handler.setFormatter(DevFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the vektra namespace."""
    return logging.getLogger(f"vektra.{name}")
