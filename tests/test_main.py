"""Tests for ``main.py``.

These tests cover the dual-conversion default mode, the user-overridable
``--converter`` flag, and the surrounding helpers (URL parsing, PDF
validation, output integrity).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import main


# --------------------------------------------------------------------------- #
# URL parsing
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://arxiv.org/pdf/0000.00000", "0000.00000"),
        ("https://arxiv.org/pdf/1234.56789v1", "1234.56789"),
        ("https://arxiv.org/pdf/1234.56789.pdf", "1234.56789"),
        ("https://arxiv.org/abs/1234.56789", "1234.56789"),
        ("https://arxiv.org/pdf/2410.12345v3", "2410.12345"),
    ],
)
def test_extract_arxiv_id_valid(url: str, expected: str) -> None:
    assert main.extract_arxiv_id(url) == expected


def test_extract_arxiv_id_invalid() -> None:
    with pytest.raises(ValueError):
        main.extract_arxiv_id("https://example.com/foo")


def test_extract_arxiv_id_empty() -> None:
    with pytest.raises(ValueError):
        main.extract_arxiv_id("")


# --------------------------------------------------------------------------- #
# PDF validation
# --------------------------------------------------------------------------- #


def test_is_valid_pdf_true_short(tmp_path: Path) -> None:
    p = tmp_path / "ok.pdf"
    p.write_bytes(b"%PDF-1.4\nhello world\n%%EOF\n")
    assert main.is_valid_pdf(p) is True


def test_is_valid_pdf_true_long(tmp_path: Path) -> None:
    # Force the validator to seek backwards into the file.
    p = tmp_path / "big.pdf"
    p.write_bytes(b"%PDF-1.4\n" + b"x" * 4000 + b"\n%%EOF\n")
    assert main.is_valid_pdf(p) is True


def test_is_valid_pdf_bad_magic(tmp_path: Path) -> None:
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"not a pdf")
    assert main.is_valid_pdf(p) is False


def test_is_valid_pdf_truncated(tmp_path: Path) -> None:
    p = tmp_path / "trunc.pdf"
    p.write_bytes(b"%PDF-1.4\npartial")
    assert main.is_valid_pdf(p) is False


def test_is_valid_pdf_missing(tmp_path: Path) -> None:
    assert main.is_valid_pdf(tmp_path / "ghost.pdf") is False


def test_is_valid_pdf_empty(tmp_path: Path) -> None:
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    assert main.is_valid_pdf(p) is False


# --------------------------------------------------------------------------- #
# Markdown output integrity
# --------------------------------------------------------------------------- #


def test_validate_markdown_ok(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("# title\n\nbody", encoding="utf-8")
    assert main.validate_markdown(p, expected_chars=len("# title\n\nbody")) is True


def test_validate_markdown_size_mismatch(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("# short", encoding="utf-8")
    assert main.validate_markdown(p, expected_chars=999) is False


def test_validate_markdown_empty(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("   \n\n", encoding="utf-8")
    assert main.validate_markdown(p, expected_chars=5) is False


def test_validate_markdown_missing(tmp_path: Path) -> None:
    assert main.validate_markdown(tmp_path / "missing.md", expected_chars=0) is False


# --------------------------------------------------------------------------- #
# CLI parsing
# --------------------------------------------------------------------------- #


def test_parse_args_default_converter() -> None:
    args = main.parse_args(["https://arxiv.org/pdf/1234.56789"])
    assert args.url == "https://arxiv.org/pdf/1234.56789"
    assert args.converter == main.CONVERTER_BOTH
    assert args.force is False
    assert args.yes is False


def test_parse_args_explicit_converter() -> None:
    args = main.parse_args(
        ["https://arxiv.org/pdf/1234.56789", "--converter", "markitdown", "-y"]
    )
    assert args.converter == "markitdown"
    assert args.yes is True


def test_parse_args_invalid_converter() -> None:
    with pytest.raises(SystemExit):
        main.parse_args(["https://arxiv.org/pdf/1234.56789", "--converter", "nope"])


# --------------------------------------------------------------------------- #
# main() end-to-end (network + heavy backends stubbed)
# --------------------------------------------------------------------------- #


STUB_PDF = b"%PDF-1.4\nfake research paper\n%%EOF\n"
DOCLING_MARKDOWN = "# docling output\n\nFrom Docling.\n"
MARKITDOWN_MARKDOWN = "# markitdown output\n\nFrom MarkItDown.\n"


def _stub_download(url: str, destination: Path, *, force: bool = False) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(STUB_PDF)
    return destination


@pytest.fixture
def isolated_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict:
    """Redirect the module-level output directories to a temp area."""
    pdf_dir = tmp_path / "pdf"
    docling_dir = tmp_path / "docling"
    markitdown_dir = tmp_path / "markitdown"
    monkeypatch.setattr(main, "PDF_DIR", pdf_dir)
    monkeypatch.setattr(main, "DOCLING_REPO_DIR", docling_dir)
    monkeypatch.setattr(main, "MARKITDOWN_DIR", markitdown_dir)
    return {
        "pdf": pdf_dir,
        "docling": docling_dir,
        "markitdown": markitdown_dir,
    }


@pytest.fixture
def stubbed_converters(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[Path], list[Path]]:
    """Replace both converters with deterministic stubs and record calls."""
    docling_calls: list[Path] = []
    markitdown_calls: list[Path] = []

    def fake_docling(pdf_path: Path) -> str:
        docling_calls.append(pdf_path)
        return DOCLING_MARKDOWN

    def fake_markitdown(pdf_path: Path) -> str:
        markitdown_calls.append(pdf_path)
        return MARKITDOWN_MARKDOWN

    monkeypatch.setattr(main, "download_pdf", _stub_download)
    monkeypatch.setattr(main, "convert_with_docling", fake_docling)
    monkeypatch.setattr(main, "convert_with_markitdown", fake_markitdown)
    return docling_calls, markitdown_calls


def test_main_default_runs_both_converters(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    docling_calls, markitdown_calls = stubbed_converters
    rc = main.main(["https://arxiv.org/pdf/1234.56789"])

    assert rc == 0
    assert len(docling_calls) == 1
    assert len(markitdown_calls) == 1
    assert docling_calls[0].name == "1234.56789.pdf"
    assert markitdown_calls[0].name == "1234.56789.pdf"

    docling_out = isolated_dirs["docling"] / "1234.56789.md"
    markitdown_out = isolated_dirs["markitdown"] / "1234.56789.md"
    assert docling_out.read_text(encoding="utf-8") == DOCLING_MARKDOWN
    assert markitdown_out.read_text(encoding="utf-8") == MARKITDOWN_MARKDOWN

    captured = capsys.readouterr()
    assert "[ok] docling" in captured.out
    assert "[ok] markitdown" in captured.out
    assert "[done]" in captured.out


def test_main_only_docling(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
) -> None:
    docling_calls, markitdown_calls = stubbed_converters
    rc = main.main(["https://arxiv.org/pdf/1234.56789", "--converter", "docling"])

    assert rc == 0
    assert len(docling_calls) == 1
    assert markitdown_calls == []

    assert (isolated_dirs["docling"] / "1234.56789.md").exists()
    assert not (isolated_dirs["markitdown"] / "1234.56789.md").exists()


def test_main_only_markitdown(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
) -> None:
    docling_calls, markitdown_calls = stubbed_converters
    rc = main.main(["https://arxiv.org/pdf/1234.56789", "--converter", "markitdown"])

    assert rc == 0
    assert docling_calls == []
    assert len(markitdown_calls) == 1

    assert not (isolated_dirs["docling"] / "1234.56789.md").exists()
    assert (isolated_dirs["markitdown"] / "1234.56789.md").exists()


def test_main_explicit_both(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
) -> None:
    docling_calls, markitdown_calls = stubbed_converters
    rc = main.main(["https://arxiv.org/pdf/1234.56789", "--converter", "both"])

    assert rc == 0
    assert len(docling_calls) == 1
    assert len(markitdown_calls) == 1


def test_main_markitdown_directory_created(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
) -> None:
    """The markitdown/ folder must be created on demand."""
    assert not isolated_dirs["markitdown"].exists()
    rc = main.main(["https://arxiv.org/pdf/1234.56789", "--converter", "markitdown"])
    assert rc == 0
    assert isolated_dirs["markitdown"].is_dir()


def test_main_invalid_url_returns_2(
    isolated_dirs: dict,
    stubbed_converters: tuple[list[Path], list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    docling_calls, markitdown_calls = stubbed_converters
    rc = main.main(["not-a-url"])
    assert rc == 2
    assert docling_calls == []
    assert markitdown_calls == []
    assert "arXiv ID" in capsys.readouterr().err


def test_main_corrupted_pdf_returns_1(
    isolated_dirs: dict,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_converters: tuple[list[Path], list[Path]],
) -> None:
    """A downloaded file without the PDF magic must abort before conversion."""
    docling_calls, markitdown_calls = stubbed_converters

    def bad_download(url: str, destination: Path, *, force: bool = False) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"definitely not a pdf")
        return destination

    monkeypatch.setattr(main, "download_pdf", bad_download)
    rc = main.main(["https://arxiv.org/pdf/1234.56789"])
    assert rc == 1
    assert docling_calls == []
    assert markitdown_calls == []


def test_main_docling_failure_still_produces_markitdown(
    isolated_dirs: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One failing backend must not block the other."""

    def ok_markitdown(pdf_path: Path) -> str:
        return MARKITDOWN_MARKDOWN

    def boom_docling(pdf_path: Path) -> str:
        raise RuntimeError("docling boom")

    monkeypatch.setattr(main, "download_pdf", _stub_download)
    monkeypatch.setattr(main, "convert_with_docling", boom_docling)
    monkeypatch.setattr(main, "convert_with_markitdown", ok_markitdown)

    rc = main.main(["https://arxiv.org/pdf/1234.56789"])

    # Docling failed → non-zero exit, but the markitdown file still exists.
    assert rc == 1
    assert (isolated_dirs["markitdown"] / "1234.56789.md").exists()
    assert not (isolated_dirs["docling"] / "1234.56789.md").exists()


def test_main_write_permission_error(
    isolated_dirs: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A write failure in one backend must not silently succeed."""

    def ok_docling(pdf_path: Path) -> str:
        return DOCLING_MARKDOWN

    def ok_markitdown(pdf_path: Path) -> str:
        return MARKITDOWN_MARKDOWN

    def boom_write(content: str, destination: Path, *, overwrite: bool = False) -> Path:
        raise PermissionError(f"denied: {destination}")

    monkeypatch.setattr(main, "download_pdf", _stub_download)
    monkeypatch.setattr(main, "convert_with_docling", ok_docling)
    monkeypatch.setattr(main, "convert_with_markitdown", ok_markitdown)
    monkeypatch.setattr(main, "write_markdown", boom_write)

    rc = main.main(["https://arxiv.org/pdf/1234.56789"])
    assert rc == 1
