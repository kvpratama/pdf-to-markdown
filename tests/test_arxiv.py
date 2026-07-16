from __future__ import annotations

import pytest

from pdf_to_markdown.arxiv import extract_arxiv_id


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
    assert extract_arxiv_id(url) == expected


def test_extract_arxiv_id_invalid() -> None:
    with pytest.raises(ValueError):
        extract_arxiv_id("https://example.com/foo")


def test_extract_arxiv_id_empty() -> None:
    with pytest.raises(ValueError):
        extract_arxiv_id("")
