"""CLI entry point for the ingestion pipeline.

Usage:
    python -m server.ingest.cli <path_or_directory> [--strategy recursive] [--chunk-size 512]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from server.core.logging import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Vektra ingestion pipeline — extract, chunk, embed, insert"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to ingest (PDF, DOCX, HTML, MD, TXT)",
    )
    parser.add_argument(
        "--strategy",
        choices=["character", "recursive", "markdown"],
        default="recursive",
        help="Chunking strategy (default: recursive)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Target chunk size in characters (default: 512)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=64,
        help="Overlap between chunks (default: 64)",
    )

    args = parser.parse_args()
    setup_logging()

    # Resolve paths — expand directories to files
    resolved: list[str] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            for ext in ("*.pdf", "*.docx", "*.html", "*.htm", "*.md", "*.txt", "*.rst"):
                resolved.extend(str(f) for f in path.glob(ext))
        elif path.is_file():
            resolved.append(str(path))
        else:
            print(f"warning: {p} not found, skipping", file=sys.stderr)

    if not resolved:
        print("no files to ingest", file=sys.stderr)
        sys.exit(1)

    print(f"ingesting {len(resolved)} files with strategy={args.strategy}")

    from server.ingest import run

    report = asyncio.run(
        run(
            resolved,
            chunk_strategy=args.strategy,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )

    print(f"\n--- Ingestion Report ---")
    print(f"documents processed: {report.documents_processed}")
    print(f"chunks created:      {report.chunks_created}")
    print(f"chunks skipped:      {report.chunks_skipped}")
    print(f"errors:              {len(report.errors)}")
    print(f"duration:            {report.duration_seconds:.1f}s")

    if report.errors:
        print("\nerrors:")
        for err in report.errors:
            print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
