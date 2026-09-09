"""Structure-aware semantic chunking with overlap.

Three strategies:
- character: fixed-size character windows with overlap
- recursive: split by paragraphs → sentences → characters
- markdown: respect markdown headers as split points
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A raw chunk before embedding."""

    text: str
    index: int
    token_count: int = 0  # filled in by embedder

    @property
    def id_seed(self) -> str:
        """Deterministic ID seed — hash set by inserter."""
        return self.text.strip()


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Chunk]:
    """Split text into chunks using the chosen strategy."""
    if strategy == "character":
        return _chunk_character(text, chunk_size, chunk_overlap)
    elif strategy == "recursive":
        return _chunk_recursive(text, chunk_size, chunk_overlap)
    elif strategy == "markdown":
        return _chunk_markdown(text, chunk_size, chunk_overlap)
    else:
        raise ValueError(f"unknown chunking strategy: {strategy!r}")


# ── Character ─────────────────────────────────────────────────────────


def _chunk_character(
    text: str, size: int, overlap: int
) -> list[Chunk]:
    """Fixed-size character windows with overlap."""
    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = start + size
        chunk_text_val = text[start:end].strip()
        if chunk_text_val:
            chunks.append(Chunk(text=chunk_text_val, index=idx))
            idx += 1
        start += size - overlap

    return chunks


# ── Recursive ─────────────────────────────────────────────────────────


def _chunk_recursive(
    text: str, size: int, overlap: int
) -> list[Chunk]:
    """Recursively split by paragraph → sentence → character."""
    # Level 1: split by double newline (paragraphs)
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[Chunk] = []
    idx = 0

    for para in paragraphs:
        if len(para) <= size:
            chunks.append(Chunk(text=para, index=idx))
            idx += 1
        else:
            # Level 2: split by sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 <= size:
                    current = f"{current} {sent}".strip() if current else sent
                else:
                    if current:
                        chunks.append(Chunk(text=current, index=idx))
                        idx += 1
                    # If sentence itself is too big, split by character
                    if len(sent) > size:
                        sub_chunks = _chunk_character(sent, size, overlap)
                        for sc in sub_chunks:
                            sc.index = idx
                            chunks.append(sc)
                            idx += 1
                        current = ""
                    else:
                        current = sent

            if current:
                chunks.append(Chunk(text=current, index=idx))
                idx += 1

    return chunks


# ── Markdown ──────────────────────────────────────────────────────────


def _chunk_markdown(
    text: str, size: int, overlap: int
) -> list[Chunk]:
    """Split on markdown headers, then recursively chunk oversized sections."""
    # Split on headers (## or ### or #)
    sections = re.split(r"\n(?=#{1,3} )", text)
    sections = [s.strip() for s in sections if s.strip()]

    chunks: list[Chunk] = []
    idx = 0

    for section in sections:
        if len(section) <= size:
            chunks.append(Chunk(text=section, index=idx))
            idx += 1
        else:
            # Recursively chunk oversized sections
            sub_chunks = _chunk_recursive(section, size, overlap)
            for sc in sub_chunks:
                sc.index = idx
                chunks.append(sc)
                idx += 1

    return chunks
