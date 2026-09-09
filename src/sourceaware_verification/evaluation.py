"""Eight-way and factor-level metrics used in the manuscript."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import dump_json, load_jsonl
from .labels import LABELS, decisions_from_label


def _metrics(gold: list[str], predicted: list[str], labels: tuple[str, ...]) -> dict[str, Any]:
    per_class: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(g == label for g in gold),
        }
    return {
        "macro_precision": sum(float(per_class[x]["precision"]) for x in labels) / len(labels),
        "macro_recall": sum(float(per_class[x]["recall"]) for x in labels) / len(labels),
        "macro_f1": sum(float(per_class[x]["f1"]) for x in labels) / len(labels),
        "per_class": per_class,
    }


def evaluate_predictions(path: str | Path, output: str | Path | None = None) -> dict[str, Any]:
    rows = load_jsonl(path)
    gold: list[str] = []
    predicted: list[str] = []
    invalid = 0
    for line, row in enumerate(rows, 1):
        gold_label = str(row.get("gold_label", row.get("label", ""))).upper()
        if gold_label not in LABELS:
            raise ValueError(f"{path}:{line}: invalid gold label {gold_label!r}")
        prediction = str(row.get("prediction", "")).upper()
        if prediction not in LABELS:
            invalid += 1
            prediction = "INVALID"
        gold.append(gold_label)
        predicted.append(prediction)
    result = _metrics(gold, predicted, LABELS)
    factor_metrics: dict[str, Any] = {}
    names = ("veracity:image", "veracity:text", "consistency:image:text")
    for name in names:
        factor_gold = [decisions_from_label(value)[name] for value in gold]
        factor_pred = [
            decisions_from_label(value)[name] if value in LABELS else "INVALID"
            for value in predicted
        ]
        factor_metrics[name] = _metrics(factor_gold, factor_pred, ("T", "F"))
    result.update(
        {
            "total": len(rows),
            "correct": sum(g == p for g, p in zip(gold, predicted)),
            "invalid_predictions": invalid,
            "accuracy": sum(g == p for g, p in zip(gold, predicted)) / len(rows) if rows else 0.0,
            "factor_metrics": factor_metrics,
        }
    )
    if output:
        dump_json(output, result)
    return result


def evaluate_factor_predictions(
    path: str | Path, output: str | Path | None = None
) -> dict[str, Any]:
    """Evaluate only factors defined for each input modality configuration."""

    rows = load_jsonl(path)
    observed: dict[str, dict[str, list[str] | int]] = {}
    for line, row in enumerate(rows, 1):
        gold_value = row.get("gold_decisions")
        predicted_value = row.get("final_decisions")
        if not isinstance(gold_value, dict) or not isinstance(predicted_value, dict):
            raise ValueError(f"{path}:{line}: gold_decisions and final_decisions are required")
        for factor, gold in gold_value.items():
            gold_decision = str(gold).upper()
            if gold_decision not in {"T", "F"}:
                raise ValueError(f"{path}:{line}: invalid gold decision for {factor}")
            bucket = observed.setdefault(
                str(factor), {"gold": [], "predicted": [], "invalid_predictions": 0}
            )
            prediction = str(predicted_value.get(factor, "")).upper()
            if prediction not in {"T", "F"}:
                prediction = "INVALID"
                bucket["invalid_predictions"] = int(bucket["invalid_predictions"]) + 1
            bucket["gold"].append(gold_decision)  # type: ignore[union-attr]
            bucket["predicted"].append(prediction)  # type: ignore[union-attr]
    factors: dict[str, Any] = {}
    for factor, bucket in observed.items():
        metrics = _metrics(
            bucket["gold"],  # type: ignore[arg-type]
            bucket["predicted"],  # type: ignore[arg-type]
            ("T", "F"),
        )
        metrics["total"] = len(bucket["gold"])  # type: ignore[arg-type]
        metrics["invalid_predictions"] = bucket["invalid_predictions"]
        factors[factor] = metrics
    result = {"rows": len(rows), "factors": factors}
    if output:
        dump_json(output, result)
    return result
