from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.validators import is_valid_pdf, validate_markdown


def test_is_valid_pdf_true_short(tmp_path: Path) -> None:
    p = tmp_path / "ok.pdf"
    p.write_bytes(b"%PDF-1.4\nhello world\n%%EOF\n")
    assert is_valid_pdf(p) is True


def test_is_valid_pdf_true_long(tmp_path: Path) -> None:
    p = tmp_path / "big.pdf"
    p.write_bytes(b"%PDF-1.4\n" + b"x" * 4000 + b"\n%%EOF\n")
    assert is_valid_pdf(p) is True


def test_is_valid_pdf_bad_magic(tmp_path: Path) -> None:
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"not a pdf")
    assert is_valid_pdf(p) is False


def test_is_valid_pdf_truncated(tmp_path: Path) -> None:
    p = tmp_path / "trunc.pdf"
    p.write_bytes(b"%PDF-1.4\npartial")
    assert is_valid_pdf(p) is False


def test_is_valid_pdf_missing(tmp_path: Path) -> None:
    assert is_valid_pdf(tmp_path / "ghost.pdf") is False


def test_is_valid_pdf_empty(tmp_path: Path) -> None:
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    assert is_valid_pdf(p) is False


def test_validate_markdown_ok(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("# title\n\nbody", encoding="utf-8")
    assert validate_markdown(p, expected_chars=len("# title\n\nbody")) is True


def test_validate_markdown_size_mismatch(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("# short", encoding="utf-8")
    assert validate_markdown(p, expected_chars=999) is False


def test_validate_markdown_empty(tmp_path: Path) -> None:
    p = tmp_path / "ok.md"
    p.write_text("   \n\n", encoding="utf-8")
    assert validate_markdown(p, expected_chars=5) is False


def test_validate_markdown_missing(tmp_path: Path) -> None:
    assert validate_markdown(tmp_path / "missing.md", expected_chars=0) is False
