from __future__ import annotations

from pdf_to_markdown.converters.registry import get_converter, get_converter_names


def test_get_converter_names_lists_supported_backends() -> None:
    assert get_converter_names() == ("docling", "markitdown")


def test_get_converter_returns_markitdown_adapter() -> None:
    converter = get_converter("markitdown")
    assert converter.name == "markitdown"
    assert converter.output_dir_attr == "markitdown_dir"
