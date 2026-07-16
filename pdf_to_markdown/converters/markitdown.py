from __future__ import annotations

from pathlib import Path


def convert_with_markitdown(pdf_path: Path) -> str:
    """Run MarkItDown on ``pdf_path`` and return Markdown text."""
    try:
        from markitdown import MarkItDown
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "MarkItDown is not installed. Run `uv add markitdown` to install it."
        ) from exc

    print(f"[markitdown] Converting {pdf_path} to Markdown ...")
    try:
        result = MarkItDown().convert(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - backend raises broad errors
        raise RuntimeError(f"MarkItDown failed on {pdf_path}: {exc}") from exc

    text = getattr(result, "text_content", None)
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("MarkItDown produced empty Markdown output.")
    return text
