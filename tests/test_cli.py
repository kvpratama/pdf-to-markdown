from __future__ import annotations

import main

from pdf_to_markdown import cli
from pdf_to_markdown.config import CONVERTER_BOTH


def test_parse_args_default_converter() -> None:
    args = cli.parse_args(["https://arxiv.org/pdf/1234.56789"])
    assert args.url == "https://arxiv.org/pdf/1234.56789"
    assert args.converter == CONVERTER_BOTH
    assert args.force is False
    assert args.yes is False


def test_parse_args_explicit_converter() -> None:
    args = cli.parse_args(
        ["https://arxiv.org/pdf/1234.56789", "--converter", "markitdown", "-y"]
    )
    assert args.converter == "markitdown"
    assert args.yes is True


def test_main_shim_delegates_to_package_cli(monkeypatch) -> None:
    seen: list[list[str] | None] = []

    def fake_main(argv: list[str] | None = None) -> int:
        seen.append(argv)
        return 7

    monkeypatch.setattr(cli, "main", fake_main)

    assert main.main(["--help"]) == 7
    assert seen == [["--help"]]


def test_parse_args_accepts_arbitrary_pdf_url() -> None:
    args = cli.parse_args(["https://example.com/paper.pdf"])
    assert args.url == "https://example.com/paper.pdf"
    assert args.converter == CONVERTER_BOTH
