from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.storage import ensure_directory, write_markdown


def test_ensure_directory_creates_nested_path(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "c"
    ensure_directory(target)
    assert target.is_dir()


def test_write_markdown_overwrites_when_flag_is_set(tmp_path: Path) -> None:
    destination = tmp_path / "paper.md"
    destination.write_text("old", encoding="utf-8")

    result = write_markdown("new", destination, overwrite=True)

    assert result == destination
    assert destination.read_text(encoding="utf-8") == "new"


def test_write_markdown_keeps_existing_file_when_confirmation_declines(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "paper.md"
    destination.write_text("old", encoding="utf-8")

    def confirm(path: Path) -> bool:
        assert path == destination
        return False

    result = write_markdown("new", destination, confirm_overwrite=confirm)

    assert result == destination
    assert destination.read_text(encoding="utf-8") == "old"
