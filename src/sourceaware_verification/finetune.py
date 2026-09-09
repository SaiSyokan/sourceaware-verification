"""Convert labeled image-text pairs into factor-specific supervision instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import dump_jsonl, load_jsonl
from .labels import decisions_from_label


INSTRUCTIONS = {
    "veracity:image": "Determine whether the image contains a factual violation according to the operational definition of image veracity.",
    "veracity:text": "Determine whether the text contains a factual violation according to the operational definition of text veracity.",
    "consistency:image:text": "Determine whether the image and text are semantically consistent, without judging their standalone factual veracity.",
}


def factor_instances(row: dict[str, Any]) -> list[dict[str, Any]]:
    sample_id = str(row["sample_id"])
    decisions = decisions_from_label(str(row["label"]))
    return [
        {
            "instance_id": f"{sample_id}--image-veracity",
            "sample_id": sample_id,
            "factor": "veracity:image",
            "image_path": row["image_path"],
            "instruction": INSTRUCTIONS["veracity:image"],
            "target": decisions["veracity:image"],
        },
        {
            "instance_id": f"{sample_id}--text-veracity",
            "sample_id": sample_id,
            "factor": "veracity:text",
            "text": row["text"],
            "instruction": INSTRUCTIONS["veracity:text"],
            "target": decisions["veracity:text"],
        },
        {
            "instance_id": f"{sample_id}--image-text-consistency",
            "sample_id": sample_id,
            "factor": "consistency:image:text",
            "image_path": row["image_path"],
            "text": row["text"],
            "instruction": INSTRUCTIONS["consistency:image:text"],
            "target": decisions["consistency:image:text"],
        },
    ]


def prepare_factor_dataset(manifest: str | Path, output: str | Path) -> int:
    instances = []
    for row in load_jsonl(manifest):
        if not row.get("image_path") or not str(row.get("text", "")).strip():
            raise ValueError(f"{row.get('sample_id')}: factor fine-tuning requires image-text input")
        instances.extend(factor_instances(row))
    dump_jsonl(output, instances)
    return len(instances)

