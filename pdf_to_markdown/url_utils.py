from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

ARXIV_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)


def _try_arxiv_id(url: str) -> str | None:
    """Return the arXiv identifier if *url* contains one, else ``None``."""
    match = ARXIV_ID_PATTERN.search(url)
    return match.group(1) if match else None


def _stem_from_url(url: str) -> str | None:
    """Extract the filename stem from the URL path, if present."""
    parsed = urlparse(url)
    path = PurePosixPath(parsed.path)
    if path.stem and path.stem != "/" and path.stem != ".":
        return path.stem
    return None


def _hash_url(url: str) -> str:
    """Return a short SHA-256 hex digest of *url* for use as a fallback id."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def extract_doc_id(url: str) -> str:
    """Derive a filesystem-safe document identifier from *url*.

    Strategy (first match wins):
    1. If the URL contains an arXiv ID, return that.
    2. If the URL path has a filename, return its stem.
    3. Otherwise, return a truncated SHA-256 hash of the full URL.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    arxiv_id = _try_arxiv_id(url)
    if arxiv_id is not None:
        return arxiv_id

    stem = _stem_from_url(url)
    if stem is not None:
        return stem

    return _hash_url(url)
