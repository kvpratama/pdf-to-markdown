from __future__ import annotations

import re

ARXIV_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)


def extract_arxiv_id(url: str) -> str:
    """Extract the arXiv identifier from a URL."""
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    match = ARXIV_ID_PATTERN.search(url)
    if not match:
        raise ValueError(
            f"Could not find an arXiv ID in the URL: {url!r}. "
            "Expected something like 'https://arxiv.org/pdf/0000.00000'."
        )
    return match.group(1)
