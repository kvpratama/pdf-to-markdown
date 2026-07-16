from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

OverwritePrompt = Callable[[Path], bool]


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


def prompt_for_overwrite(destination: Path) -> bool:
    """Ask the user if an existing destination should be overwritten."""
    try:
        answer = (
            input(f"Markdown file already exists at {destination}. Overwrite? [y/N]: ")
            .strip()
            .lower()
        )
    except EOFError as exc:
        raise RuntimeError(
            "Overwrite confirmation unavailable (non-interactive shell); "
            "rerun with --yes to force the overwrite."
        ) from exc
    return answer in {"y", "yes"}


def write_markdown(
    content: str,
    destination: Path,
    *,
    overwrite: bool = False,
    confirm_overwrite: OverwritePrompt | None = None,
    log: Callable[[str], None] = print,
) -> Path:
    """Write ``content`` to ``destination`` with UTF-8 encoding."""
    ensure_directory(destination.parent)

    if destination.exists() and not overwrite:
        should_overwrite = (
            confirm_overwrite(destination)
            if confirm_overwrite is not None
            else prompt_for_overwrite(destination)
        )
        if not should_overwrite:
            log("[skip] Keeping existing Markdown file.")
            return destination

    try:
        destination.write_text(content, encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write Markdown to {destination}: permission denied."
        ) from exc
    except OSError as exc:
        raise OSError(f"Failed to write Markdown to {destination}: {exc}") from exc

    log(f"[save] Wrote {len(content):,} chars to {destination}")
    return destination
