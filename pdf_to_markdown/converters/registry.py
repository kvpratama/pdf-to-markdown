from __future__ import annotations

from pdf_to_markdown.config import (
    ALL_CONVERTERS,
    CONVERTER_DOCLING,
    CONVERTER_MARKITDOWN,
)
from pdf_to_markdown.converters.base import ConverterAdapter
from pdf_to_markdown.converters.docling import convert_with_docling
from pdf_to_markdown.converters.markitdown import convert_with_markitdown


def _registry() -> dict[str, ConverterAdapter]:
    return {
        CONVERTER_DOCLING: ConverterAdapter(
            name=CONVERTER_DOCLING,
            output_dir_attr="docling_dir",
            convert=convert_with_docling,
        ),
        CONVERTER_MARKITDOWN: ConverterAdapter(
            name=CONVERTER_MARKITDOWN,
            output_dir_attr="markitdown_dir",
            convert=convert_with_markitdown,
        ),
    }


def get_converter(name: str) -> ConverterAdapter:
    try:
        return _registry()[name]
    except KeyError as exc:
        raise KeyError(f"Unknown converter: {name}") from exc


def get_converter_names() -> tuple[str, ...]:
    return ALL_CONVERTERS
