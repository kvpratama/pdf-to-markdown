from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from pdf_to_markdown.storage import ensure_directory


def download_pdf(
    url: str,
    destination: Path,
    *,
    force: bool = False,
    user_agent: str,
    timeout_seconds: int,
    log: Callable[[str], None] = print,
) -> Path:
    """Download the PDF at ``url`` to ``destination``."""
    ensure_directory(destination.parent)

    if destination.exists() and not force:
        log(f"[skip] PDF already present at {destination}")
        return destination

    log(f"[download] Fetching {url} ...")
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = response.read()
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
            f"Timed out after {timeout_seconds}s while downloading {url}."
        ) from exc

    try:
        destination.write_bytes(data)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write PDF to {destination}: permission denied."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to write PDF to {destination}: {exc}") from exc

    log(f"[download] Saved {len(data):,} bytes to {destination}")
    return destination
