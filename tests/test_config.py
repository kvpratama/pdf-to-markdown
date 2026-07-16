from __future__ import annotations

from pdf_to_markdown.config import AppConfig


def test_default_config_uses_project_relative_directories() -> None:
    config = AppConfig.default()
    assert config.pdf_dir.name == "pdf"
    assert config.docling_dir.name == "docling"
    assert config.markitdown_dir.name == "markitdown"
