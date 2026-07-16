from __future__ import annotations

import pytest
import typing

from pdf_to_markdown.url_utils import extract_doc_id


# --- arXiv URLs should still produce the arXiv identifier ----


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://arxiv.org/pdf/1234.56789", "1234.56789"),
        ("https://arxiv.org/pdf/2410.12345v3", "2410.12345"),
        ("https://arxiv.org/abs/0000.00000", "0000.00000"),
    ],
)
def test_extract_doc_id_arxiv_urls(url: str, expected: str) -> None:
    assert extract_doc_id(url) == expected


# --- Arbitrary PDF URLs should derive the id from the filename stem ---


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://example.com/paper.pdf", "paper"),
        ("https://example.com/docs/my-report.pdf", "my-report"),
        ("https://example.com/path/to/whitepaper.pdf?v=2", "whitepaper"),
        ("https://example.com/UPPER_CASE.PDF", "UPPER_CASE"),
    ],
)
def test_extract_doc_id_arbitrary_pdf_urls(url: str, expected: str) -> None:
    assert extract_doc_id(url) == expected


# --- URLs with no usable filename fall back to a URL hash ---


def test_extract_doc_id_no_filename_uses_hash() -> None:
    doc_id = extract_doc_id("https://example.com/")
    # Should be a non-empty hex string (hash-based identifier).
    assert doc_id
    assert isinstance(doc_id, str)
    assert len(doc_id) > 0


def test_extract_doc_id_hash_is_deterministic() -> None:
    url = "https://example.com/generate?id=42"
    assert extract_doc_id(url) == extract_doc_id(url)


# --- Edge cases ---


def test_extract_doc_id_empty_raises() -> None:
    with pytest.raises(ValueError):
        extract_doc_id("")


def test_extract_doc_id_none_raises() -> None:
    with pytest.raises(ValueError):
        extract_doc_id(typing.cast(str, None))
