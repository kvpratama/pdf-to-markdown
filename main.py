"""Command-line tool to download an arXiv PDF and convert it to Markdown via Docling.

Usage:
    uv run main.py https://arxiv.org/pdf/0000.00000
    uv run main.py https://arxiv.org/pdf/0000.00000 --force
    uv run main.py https://arxiv.org/pdf/0000.00000 --yes

The script:
  1. Parses the arXiv URL and extracts the arXiv ID.
  2. Downloads the PDF to the local ``pdf/`` folder (skipped if already present,
     unless ``--force`` is supplied).
  3. Validates the downloaded file is a non-corrupted PDF (checks magic bytes
     and ``%%EOF`` trailer).
  4. Runs Docling to convert the PDF into Markdown and writes the result to
     ``docling/`` (auto-created).  If the Markdown already exists the user
     is prompted before overwriting (``--yes`` skips the prompt).
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent
PDF_DIR = PROJECT_ROOT / "pdf"
DOCLING_REPO_DIR = PROJECT_ROOT / "docling"

# arXiv identifiers look like ``1234.56789`` (with an optional version such as
# ``v1`` or ``v3``).  The PDF URL form is ``/pdf/<id>`` (optionally ``.pdf``).
ARXIV_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
PDF_MAGIC = b"%PDF-"
PDF_TIMEOUT_SECONDS = 60

USER_AGENT = "pdf-to-markdown/0.1 (+https://arxiv.org)"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("Download an arXiv PDF and convert it to Markdown with Docling.")
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
        help="Overwrite the existing Markdown file without prompting.",
    )
    return parser.parse_args(argv)


def extract_arxiv_id(url: str) -> str:
    """Extract the arXiv identifier from a URL.

    Accepts forms such as:
      * https://arxiv.org/pdf/0000.00000
      * https://arxiv.org/pdf/0000.00000v1
      * https://arxiv.org/pdf/0000.00000.pdf
      * https://arxiv.org/abs/0000.00000

    Raises ``ValueError`` when no identifier is found.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    match = ARXIV_ID_PATTERN.search(url)
    if not match:
        raise ValueError(
            f"Could not find an arXiv ID in the URL: {url!r}. "
            "Expected something like 'https://arxiv.org/pdf/0000.00000'."
        )
    return match.group(1)


def ensure_directory(path: Path) -> None:
    """Create ``path`` (including parents) with mode 0o755 if missing."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot create directory {path}: permission denied."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to create directory {path}: {exc}") from exc


def download_pdf(url: str, destination: Path, *, force: bool = False) -> Path:
    """Download the PDF at ``url`` to ``destination``.

    Skips the network call if the file already exists, unless ``force`` is
    True.  Validates the magic bytes and ``%%EOF`` trailer before returning.
    """
    ensure_directory(destination.parent)

    if destination.exists() and not force:
        print(f"[skip] PDF already present at {destination}")
        return destination

    print(f"[download] Fetching {url} ...")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=PDF_TIMEOUT_SECONDS) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"HTTP {exc.code} {exc.reason} while downloading {url}."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error while downloading {url}: {exc.reason}."
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            f"Timed out after {PDF_TIMEOUT_SECONDS}s while downloading {url}."
        ) from exc

    try:
        destination.write_bytes(data)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write PDF to {destination}: permission denied."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to write PDF to {destination}: {exc}") from exc

    print(f"[download] Saved {len(data):,} bytes to {destination}")
    return destination


def is_valid_pdf(path: Path) -> bool:
    """Lightweight check that ``path`` looks like a real, complete PDF."""
    if not path.is_file() or path.stat().st_size == 0:
        return False

    try:
        head = path.read_bytes()[:5]
    except OSError:
        return False
    if not head.startswith(PDF_MAGIC):
        return False

    # PDF spec mandates a ``%%EOF`` marker (optionally followed by a newline)
    # as the last bytes of the file.  Inspect the tail to confirm.
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - 1024), 0)  # SEEK_SET; clamp to start
            tail = fh.read()
    except OSError:
        return False
    return b"%%EOF" in tail


def convert_with_docling(pdf_path: Path) -> str:
    """Run Docling on ``pdf_path`` and return the generated Markdown text."""
    # Imported lazily so the rest of the script can be parsed even if Docling
    # is not installed (helpful for unit testing and for fast --help).
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Docling is not installed. Run `uv add docling` to install it."
        ) from exc

    print(f"[docling] Converting {pdf_path} to Markdown ...")
    converter = DocumentConverter()
    try:
        result = converter.convert(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - Docling raises broad errors
        raise RuntimeError(f"Docling failed on {pdf_path}: {exc}") from exc

    document = getattr(result, "document", None)
    if document is None or not hasattr(document, "export_to_markdown"):
        raise RuntimeError(
            "Docling returned an unexpected result object; cannot export Markdown."
        )

    markdown = document.export_to_markdown()
    if not isinstance(markdown, str) or not markdown.strip():
        raise RuntimeError("Docling produced empty Markdown output.")
    return markdown


def write_markdown(
    content: str,
    destination: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``content`` to ``destination`` with UTF-8 encoding.

    When the file already exists the user is asked to confirm overwriting,
    unless ``overwrite`` is True.  An EOF / Ctrl-D response aborts the write.
    """
    ensure_directory(destination.parent)

    if destination.exists() and not overwrite:
        try:
            answer = (
                input(
                    f"Markdown file already exists at {destination}. Overwrite? [y/N]: "
                )
                .strip()
                .lower()
            )
        except EOFError as exc:
            raise RuntimeError(
                "Overwrite confirmation unavailable (non-interactive shell); "
                "rerun with --yes to force the overwrite."
            ) from exc
        if answer not in {"y", "yes"}:
            print("[skip] Keeping existing Markdown file.")
            return destination

    try:
        destination.write_text(content, encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write Markdown to {destination}: permission denied."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to write Markdown to {destination}: {exc}") from exc

    print(f"[save] Wrote {len(content):,} chars to {destination}")
    return destination


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        arxiv_id = extract_arxiv_id(args.url)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
    md_path = DOCLING_REPO_DIR / f"{arxiv_id}.md"

    try:
        # Step 1: ensure both target directories exist with sane permissions.
        ensure_directory(PDF_DIR)
        ensure_directory(DOCLING_REPO_DIR)

        # Step 2: download the PDF (idempotent unless --force).
        pdf_path = download_pdf(args.url, pdf_path, force=args.force)

        # Step 3: validate the PDF before handing it to Docling.
        if not is_valid_pdf(pdf_path):
            print(
                f"[error] {pdf_path} is not a valid PDF (bad magic or "
                "missing %%EOF marker).",
                file=sys.stderr,
            )
            return 1

        # Step 4: run Docling to obtain Markdown.
        markdown = convert_with_docling(pdf_path)

        # Step 5: persist the Markdown, prompting for overwrite if needed.
        write_markdown(markdown, md_path, overwrite=args.yes)
    except PermissionError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except (RuntimeError, OSError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[done] Workflow completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
