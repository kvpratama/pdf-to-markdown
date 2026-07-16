from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConverterAdapter:
    name: str
    output_dir_attr: str
    convert: Callable[[Path], str]
