"""Typed records for the source-aware factor space."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


MODALITY_ORDER = ("image", "text", "audio", "video")


def modality_sort_key(name: str) -> tuple[int, str]:
    normalized = name.strip().lower()
    try:
        return MODALITY_ORDER.index(normalized), normalized
    except ValueError:
        return len(MODALITY_ORDER), normalized


@dataclass(frozen=True, order=True)
class FactorKey:
    """A modality-veracity or pairwise-consistency target."""

    kind: str
    left: str
    right: str | None = None

    def __post_init__(self) -> None:
        kind = self.kind.strip().lower()
        left = self.left.strip().lower()
        right = self.right.strip().lower() if self.right else None
        if kind not in {"veracity", "consistency"}:
            raise ValueError(f"unsupported factor kind: {self.kind!r}")
        if not left:
            raise ValueError("factor modality must not be empty")
        if kind == "veracity" and right is not None:
            raise ValueError("a veracity factor has exactly one modality")
        if kind == "consistency":
            if not right or right == left:
                raise ValueError("a consistency factor requires two distinct modalities")
            if modality_sort_key(right) < modality_sort_key(left):
                left, right = right, left
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)

    @property
    def id(self) -> str:
        if self.kind == "veracity":
            return f"veracity:{self.left}"
        return f"consistency:{self.left}:{self.right}"

    @property
    def display_name(self) -> str:
        if self.kind == "veracity":
            return f"{self.left.title()} Veracity"
        return f"{self.left.title()}-{str(self.right).title()} Consistency"

    @classmethod
    def from_id(cls, value: str) -> "FactorKey":
        parts = value.strip().lower().split(":")
        if len(parts) == 2:
            return cls(parts[0], parts[1])
        if len(parts) == 3:
            return cls(parts[0], parts[1], parts[2])
        raise ValueError(f"invalid factor id: {value!r}")


@dataclass(frozen=True)
class FactorResult:
    decision: str
    confidence: float
    explanation: str
    raw_output: str = ""

    def __post_init__(self) -> None:
        decision = self.decision.strip().upper()
        if decision not in {"T", "F"}:
            raise ValueError("factor decision must be T or F")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("factor confidence must be in [0, 1]")
        if not self.explanation.strip():
            raise ValueError("factor explanation must not be empty")
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "confidence", float(self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuredPrediction:
    sample_id: str
    modalities: tuple[str, ...]
    module_outputs: Mapping[str, FactorResult]
    final_decisions: Mapping[str, str]
    label: str | None = None
    image_description: str = ""
    verification_questions: tuple[str, ...] = ()
    aggregator_output: str = ""
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "modalities": list(self.modalities),
            "module_outputs": {
                key: value.to_dict() for key, value in self.module_outputs.items()
            },
            "final_decisions": dict(self.final_decisions),
            "label": self.label,
            "image_description": self.image_description,
            "verification_questions": list(self.verification_questions),
            "aggregator_output": self.aggregator_output,
            "error": self.error,
            "metadata": dict(self.metadata),
        }

