"""Generation backend contract used by the verification pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Backend(Protocol):
    def generate(self, prompt: str, image_path: str | Path | None = None) -> str: ...

