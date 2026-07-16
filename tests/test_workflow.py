from __future__ import annotations

from pathlib import Path
from collections.abc import Callable as callable

import pytest

from pdf_to_markdown.config import AppConfig, CONVERTER_DOCLING, CONVERTER_MARKITDOWN
from pdf_to_markdown.models import WorkflowResult
from pdf_to_markdown.workflow import run_workflow

STUB_PDF = b"%PDF-1.4\nfake research paper\n%%EOF\n"
DOCLING_MARKDOWN = "# docling output\n\nFrom Docling.\n"
MARKITDOWN_MARKDOWN = "# markitdown output\n\nFrom MarkItDown.\n"


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        project_root=tmp_path,
        pdf_dir=tmp_path / "pdf",
        docling_dir=tmp_path / "docling",
        markitdown_dir=tmp_path / "markitdown",
    )


@pytest.fixture
def fake_download() -> callable:
    def _download(
        url: str,
        destination: Path,
        *,
        force: bool = False,
        user_agent: str,
        timeout_seconds: int,
    ) -> Path:
        del url, force, user_agent, timeout_seconds
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(STUB_PDF)
        return destination

    return _download


def test_run_workflow_runs_both_converters_by_default(
    app_config: AppConfig,
    fake_download: callable,
) -> None:
    docling_calls: list[Path] = []
    markitdown_calls: list[Path] = []

    def docling_convert(pdf_path: Path) -> str:
        docling_calls.append(pdf_path)
        return DOCLING_MARKDOWN

    def markitdown_convert(pdf_path: Path) -> str:
        markitdown_calls.append(pdf_path)
        return MARKITDOWN_MARKDOWN

    result = run_workflow(
        url="https://arxiv.org/pdf/1234.56789",
        selected_converters=None,
        force=False,
        overwrite=True,
        config=app_config,
        converters={
            CONVERTER_DOCLING: docling_convert,
            CONVERTER_MARKITDOWN: markitdown_convert,
        },
        download_pdf_fn=fake_download,
    )

    assert isinstance(result, WorkflowResult)
    assert result.exit_code == 0
    assert docling_calls == [app_config.pdf_dir / "1234.56789.pdf"]
    assert markitdown_calls == [app_config.pdf_dir / "1234.56789.pdf"]
    assert result.outputs[CONVERTER_DOCLING] == app_config.docling_dir / "1234.56789.md"
    assert (
        result.outputs[CONVERTER_MARKITDOWN]
        == app_config.markitdown_dir / "1234.56789.md"
    )


def test_run_workflow_returns_two_for_empty_url(
    app_config: AppConfig,
    fake_download: callable,
) -> None:
    result = run_workflow(
        url="",
        selected_converters=None,
        force=False,
        overwrite=False,
        config=app_config,
        converters={},
        download_pdf_fn=fake_download,
    )

    assert result.exit_code == 2
    assert result.failed_converters == []


def test_run_workflow_continues_when_one_converter_fails(
    app_config: AppConfig,
    fake_download: callable,
) -> None:
    def boom_docling(pdf_path: Path) -> str:
        del pdf_path
        raise RuntimeError("docling boom")

    def ok_markitdown(pdf_path: Path) -> str:
        del pdf_path
        return MARKITDOWN_MARKDOWN

    result = run_workflow(
        url="https://arxiv.org/pdf/1234.56789",
        selected_converters=[CONVERTER_DOCLING, CONVERTER_MARKITDOWN],
        force=False,
        overwrite=True,
        config=app_config,
        converters={
            CONVERTER_DOCLING: boom_docling,
            CONVERTER_MARKITDOWN: ok_markitdown,
        },
        download_pdf_fn=fake_download,
    )

    assert result.exit_code == 1
    assert result.failed_converters == [CONVERTER_DOCLING]
    assert (
        result.outputs[CONVERTER_MARKITDOWN]
        == app_config.markitdown_dir / "1234.56789.md"
    )


def test_run_workflow_accepts_arbitrary_pdf_url(
    app_config: AppConfig,
    fake_download: callable,
) -> None:
    def stub_convert(pdf_path: Path) -> str:
        del pdf_path
        return DOCLING_MARKDOWN

    result = run_workflow(
        url="https://example.com/papers/my-report.pdf",
        selected_converters=[CONVERTER_DOCLING],
        force=False,
        overwrite=True,
        config=app_config,
        converters={CONVERTER_DOCLING: stub_convert},
        download_pdf_fn=fake_download,
    )

    assert result.exit_code == 0
    assert result.doc_id == "my-report"
    assert result.pdf_path == app_config.pdf_dir / "my-report.pdf"
    assert result.outputs[CONVERTER_DOCLING] == app_config.docling_dir / "my-report.md"


def test_run_workflow_arxiv_url_sets_doc_id(
    app_config: AppConfig,
    fake_download: callable,
) -> None:
    def stub_convert(pdf_path: Path) -> str:
        del pdf_path
        return DOCLING_MARKDOWN

    result = run_workflow(
        url="https://arxiv.org/pdf/1234.56789",
        selected_converters=[CONVERTER_DOCLING],
        force=False,
        overwrite=True,
        config=app_config,
        converters={CONVERTER_DOCLING: stub_convert},
        download_pdf_fn=fake_download,
    )

    assert result.exit_code == 0
    assert result.doc_id == "1234.56789"
