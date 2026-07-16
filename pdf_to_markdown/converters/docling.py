from __future__ import annotations

from pathlib import Path


def convert_with_docling(pdf_path: Path) -> str:
    """Run Docling on ``pdf_path`` and return the generated Markdown text."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Docling is not installed. Run `uv add docling` to install it."
        ) from exc

    print(f"[docling] Converting {pdf_path} to Markdown ...")
    converter = DocumentConverter()
    try:
        result = converter.convert(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - backend raises broad errors
        raise RuntimeError(f"Docling failed on {pdf_path}: {exc}") from exc

    document = getattr(result, "document", None)
    if document is None or not hasattr(document, "export_to_markdown"):
        raise RuntimeError(
            "Docling returned an unexpected result object; cannot export Markdown."
        )

    markdown = document.export_to_markdown()
    if not isinstance(markdown, str) or not markdown.strip():
        raise RuntimeError("Docling produced empty Markdown output.")
    return markdown
