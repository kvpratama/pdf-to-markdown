from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CONVERTER_BOTH = "both"
CONVERTER_DOCLING = "docling"
CONVERTER_MARKITDOWN = "markitdown"
ALL_CONVERTERS = (CONVERTER_DOCLING, CONVERTER_MARKITDOWN)

PDF_TIMEOUT_SECONDS = 60
USER_AGENT = "pdf-to-markdown/0.1 (+https://arxiv.org)"


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    pdf_dir: Path
    docling_dir: Path
    markitdown_dir: Path
    user_agent: str = USER_AGENT
    pdf_timeout_seconds: int = PDF_TIMEOUT_SECONDS

    @classmethod
    def default(cls) -> "AppConfig":
        project_root = Path(__file__).resolve().parent.parent
        return cls(
            project_root=project_root,
            pdf_dir=project_root / "pdf",
            docling_dir=project_root / "docling",
            markitdown_dir=project_root / "markitdown",
        )

    def output_dir_for(self, converter_name: str) -> Path:
        if converter_name == CONVERTER_DOCLING:
            return self.docling_dir
        if converter_name == CONVERTER_MARKITDOWN:
            return self.markitdown_dir
        raise KeyError(f"Unknown converter: {converter_name}")
