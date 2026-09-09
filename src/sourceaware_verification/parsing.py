"""Strict parsing for factor modules and structured aggregation."""

from __future__ import annotations

import json
import re
from typing import Iterable

from .schema import FactorKey, FactorResult


def _json_dict(raw: str) -> dict[str, object] | None:
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def parse_factor(raw: str) -> FactorResult:
    value = _json_dict(raw)
    if value is not None:
        decision = str(value.get("decision", ""))
        confidence = value.get("confidence")
        explanation = str(value.get("explanation", ""))
    else:
        decision_match = re.search(r"(?im)^\s*Decision\s*:\s*(T|F|True|False)\s*$", raw)
        confidence_match = re.search(
            r"(?im)^\s*Confidence\s*:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
            raw,
        )
        explanation_match = re.search(r"(?ims)^\s*Explanation\s*:\s*(.+?)\s*$", raw)
        if not decision_match or not confidence_match or not explanation_match:
            raise ValueError("factor output does not follow the required protocol")
        decision = decision_match.group(1)
        confidence = confidence_match.group(1)
        explanation = explanation_match.group(1)
    decision = {"TRUE": "T", "FALSE": "F"}.get(decision.strip().upper(), decision.strip().upper())
    try:
        score = float(confidence)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError("factor confidence must be numeric") from exc
    return FactorResult(decision, score, explanation.strip(), raw)


def parse_questions(raw: str) -> tuple[str, ...]:
    lines = []
    for line in raw.splitlines():
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        if cleaned and cleaned.lower() not in {"questions:", "output:"}:
            lines.append(cleaned)
    if not lines:
        raise ValueError("question generator returned no usable question")
    return tuple(lines[:2])


def parse_structured_decisions(raw: str, factors: Iterable[FactorKey]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for factor in factors:
        pattern = rf"(?im)^\s*{re.escape(factor.display_name)}\s*:\s*(T|F|True|False)\s*$"
        match = re.search(pattern, raw)
        if not match:
            raise ValueError(f"aggregator omitted {factor.display_name}")
        parsed[factor.id] = {"TRUE": "T", "FALSE": "F"}.get(
            match.group(1).upper(), match.group(1).upper()
        )
    return parsed


def parse_label(raw: str) -> str:
    match = re.search(r"(?im)^\s*Label\s*:\s*([TF]{3})\s*$", raw)
    if not match:
        raise ValueError("holistic output does not contain a valid Label line")
    return match.group(1).upper()
