from __future__ import annotations

import sys
from pathlib import Path

PDF_MAGIC = b"%PDF-"


def is_valid_pdf(path: Path) -> bool:
    """Lightweight check that ``path`` looks like a real, complete PDF."""
    if not path.is_file() or path.stat().st_size == 0:
        return False

    try:
        head = path.read_bytes()[:5]
    except OSError:
        return False
    if not head.startswith(PDF_MAGIC):
        return False

    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - 1024), 0)
            tail = fh.read()
    except OSError:
        return False
    return b"%%EOF" in tail


def validate_markdown(path: Path, *, expected_chars: int) -> bool:
    """Verify ``path`` is a non-empty Markdown file matching what was written."""
    if not path.is_file():
        print(f"[error] Output file missing after write: {path}", file=sys.stderr)
        return False
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[error] Cannot re-read {path}: {exc}", file=sys.stderr)
        return False
    if not content.strip():
        print(f"[error] Output file is empty: {path}", file=sys.stderr)
        return False
    if len(content) != expected_chars:
        print(
            f"[error] Output file size mismatch at {path}: "
            f"expected {expected_chars} chars, found {len(content)}.",
            file=sys.stderr,
        )
        return False
    return True
