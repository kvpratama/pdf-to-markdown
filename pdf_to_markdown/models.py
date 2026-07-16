from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class WorkflowResult:
    exit_code: int
    outputs: dict[str, Path | None] = field(default_factory=dict)
    failed_converters: list[str] = field(default_factory=list)
    arxiv_id: str | None = None
    pdf_path: Path | None = None
