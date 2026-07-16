from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from pdf_to_markdown.config import (
    ALL_CONVERTERS,
    AppConfig,
    CONVERTER_BOTH,
)
from pdf_to_markdown.converters.registry import get_converter
from pdf_to_markdown.workflow import run_workflow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Download an arXiv PDF and convert it to Markdown. "
            "Runs both Docling and MarkItDown by default."
        )
    )
    parser.add_argument(
        "url",
        help="arXiv PDF URL, e.g. https://arxiv.org/pdf/0000.00000",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download the PDF even if it already exists locally.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Overwrite existing Markdown files without prompting.",
    )
    parser.add_argument(
        "--converter",
        choices=[CONVERTER_BOTH, *ALL_CONVERTERS],
        default=CONVERTER_BOTH,
        help=(
            "Which converter(s) to run. Default: %(default)s, which runs both "
            "Docling and MarkItDown so the outputs can be compared."
        ),
    )
    return parser.parse_args(argv)


def _err_log(message: str) -> None:
    print(message, file=sys.stderr)


def _build_converters(selected: list[str]) -> dict[str, Callable[[Path], str]]:
    return {name: get_converter(name).convert for name in selected}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    selected = (
        list(ALL_CONVERTERS) if args.converter == CONVERTER_BOTH else [args.converter]
    )
    result = run_workflow(
        url=args.url,
        selected_converters=selected,
        force=args.force,
        overwrite=args.yes,
        config=AppConfig.default(),
        converters=_build_converters(selected),
        err_log=_err_log,
    )
    return result.exit_code
