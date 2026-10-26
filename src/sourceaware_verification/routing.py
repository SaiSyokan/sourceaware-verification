"""Input analysis and dynamic factor routing (paper Eqs. 8-10)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence

from .schema import FactorKey, modality_sort_key


FIELD_TO_MODALITY = {
    "image_path": "image",
    "text": "text",
    "audio_path": "audio",
    "video_path": "video",
}


@dataclass(frozen=True)
class Analysis:
    modalities: tuple[str, ...]
    relations: tuple[tuple[str, str], ...]


class InputAnalyzer:
    """Detect available modalities without making a truth judgment."""

    def analyze(self, row: Mapping[str, object]) -> Analysis:
        found: set[str] = set()
        explicit = row.get("modalities")
        if isinstance(explicit, Sequence) and not isinstance(explicit, (str, bytes)):
            found.update(str(item).strip().lower() for item in explicit if str(item).strip())
        for field, modality in FIELD_TO_MODALITY.items():
            value = row.get(field)
            if value is not None and str(value).strip():
                found.add(modality)
        modalities = tuple(sorted(found, key=modality_sort_key))
        if not modalities:
            raise ValueError("input contains no supported modality")
        relations = tuple(combinations(modalities, 2))
        return Analysis(modalities, relations)


class VerificationRouter:
    """Return F_X = modality veracity factors union pairwise relations."""

    def route(self, analysis: Analysis) -> tuple[FactorKey, ...]:
        factors = [FactorKey("veracity", modality) for modality in analysis.modalities]
        factors.extend(FactorKey("consistency", left, right) for left, right in analysis.relations)
        return tuple(factors)

