"""Compatibility entrypoint for the package-based CLI."""

from __future__ import annotations

from pdf_to_markdown import cli


def main(argv: list[str] | None = None) -> int:
    return cli.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
