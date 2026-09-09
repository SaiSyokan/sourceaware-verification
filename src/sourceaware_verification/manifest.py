"""Validation for image-only, text-only, and image-text manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_jsonl, validate_identifier
from .labels import LABELS
from .routing import InputAnalyzer


def validate_manifest(
    path: str | Path,
    check_files: bool = False,
    media_root: str | Path | None = None,
) -> dict[str, Any]:
    rows = load_jsonl(path)
    analyzer = InputAnalyzer()
    root = Path(media_root).expanduser().resolve() if media_root else Path(path).resolve().parent
    errors: list[str] = []
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for line, row in enumerate(rows, 1):
        try:
            sample_id = validate_identifier(row.get("sample_id"), "sample_id")
            if sample_id in seen:
                raise ValueError(f"duplicate sample_id {sample_id!r}")
            seen.add(sample_id)
            analysis = analyzer.analyze(row)
            key = "+".join(analysis.modalities)
            counts[key] = counts.get(key, 0) + 1
            label = str(row.get("label", "")).upper()
            if label and label not in LABELS:
                raise ValueError(f"invalid label {label!r}")
            axis_fields = (
                ("image_veracity", 0),
                ("text_veracity", 1),
                ("image_text_consistency", 2),
            )
            for field, position in axis_fields:
                if field not in row:
                    continue
                decision = str(row[field]).upper()
                if decision not in {"T", "F"}:
                    raise ValueError(f"invalid {field} {row[field]!r}")
                if label and decision != label[position]:
                    raise ValueError(f"{field} disagrees with label {label}")
            if check_files and "image" in analysis.modalities:
                image_path = Path(str(row["image_path"])).expanduser()
                resolved = image_path if image_path.is_absolute() else root / image_path
                if not resolved.is_file():
                    raise ValueError(f"missing image {resolved}")
        except Exception as exc:
            errors.append(f"line {line}: {exc}")
    return {"valid": not errors, "rows": len(rows), "modality_counts": counts, "errors": errors}
