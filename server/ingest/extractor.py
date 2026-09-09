"""Per-format text extraction — PDF, DOCX, HTML, Markdown, plain text."""

from __future__ import annotations

import hashlib
from pathlib import Path

from server.core.logging import get_logger

logger = get_logger("ingest.extractor")

# Supported extensions
_EXTRACTORS: dict[str, callable] = {}


def _register(ext: str):
    def decorator(fn):
        _EXTRACTORS[ext] = fn
        return fn
    return decorator


@_register(".pdf")
def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


@_register(".docx")
def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


@_register(".html")
@_register(".htm")
def _extract_html(path: Path) -> str:
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts: list[str] = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                text = data.strip()
                if text:
                    self.text_parts.append(text)

    extractor = TextExtractor()
    extractor.feed(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(extractor.text_parts)


@_register(".md")
@_register(".markdown")
def _extract_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


@_register(".txt")
@_register(".rst")
def _extract_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def content_hash(text: str) -> str:
    """Deterministic SHA-256 of content for dedup."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def extract_files(
    paths: list[str],
) -> list[tuple[str, str, str]]:
    """Extract text from files.

    Returns list of (text, filename, content_hash) tuples.
    """
    results: list[tuple[str, str, str]] = []

    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            logger.warning("file not found: %s", path)
            continue

        ext = path.suffix.lower()
        extractor = _EXTRACTORS.get(ext)
        if extractor is None:
            logger.warning("unsupported format: %s (%s)", path.name, ext)
            continue

        try:
            text = extractor(path)
            if not text.strip():
                logger.warning("empty content: %s", path.name)
                continue

            h = content_hash(text)
            results.append((text, path.name, h))
            logger.info("extracted %s (%d chars)", path.name, len(text))
        except Exception as e:
            logger.error("extraction failed for %s: %s", path.name, e)

    return results
