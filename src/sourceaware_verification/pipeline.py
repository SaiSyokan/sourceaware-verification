"""Paper-aligned source-aware verification pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .backend import Backend
from .evidence import EvidenceStore
from .labels import decisions_from_label, label_from_decisions
from .parsing import parse_factor, parse_label, parse_questions, parse_structured_decisions
from .prompts import (
    HOLISTIC_EIGHT_WAY,
    IMAGE_DESCRIPTION,
    IMAGE_TEXT_CONSISTENCY,
    IMAGE_VERACITY,
    JOINT_FACTORS,
    PROMPT_VERSION,
    STRUCTURED_AGGREGATION,
    TEXT_VERACITY,
    VERIFICATION_QUESTIONS,
)
from .routing import InputAnalyzer, VerificationRouter
from .schema import FactorKey, FactorResult, StructuredPrediction


PRIMARY_STRATEGY = "separate_structured"
STRATEGIES = (
    "holistic",
    "joint_factors",
    "separate_deterministic",
    "separate_structured",
)


class SourceAwareVerifier:
    """Execute active factor modules and aggregate their structured outputs."""

    def __init__(
        self,
        backend: Backend,
        evidence: EvidenceStore,
        *,
        use_evidence: bool = True,
        use_image_description: bool = True,
        retrieval_limit: int = 3,
    ) -> None:
        if retrieval_limit < 1:
            raise ValueError("retrieval_limit must be positive")
        self.backend = backend
        self.evidence = evidence
        self.use_evidence = use_evidence
        self.use_image_description = use_image_description
        self.retrieval_limit = retrieval_limit
        self.analyzer = InputAnalyzer()
        self.router = VerificationRouter()

    @staticmethod
    def _image_path(row: Mapping[str, object], media_root: str | Path) -> Path:
        path = Path(str(row["image_path"])).expanduser()
        return path if path.is_absolute() else Path(media_root) / path

    def predict(
        self,
        row: Mapping[str, object],
        media_root: str | Path = ".",
        strategy: str = PRIMARY_STRATEGY,
    ) -> StructuredPrediction:
        if strategy not in STRATEGIES:
            raise ValueError(f"unsupported strategy: {strategy!r}")
        sample_id = str(row.get("sample_id", "")).strip()
        if not sample_id:
            raise ValueError("sample_id is required")
        analysis = self.analyzer.analyze(row)
        unsupported = set(analysis.modalities) - {"image", "text"}
        if unsupported:
            raise NotImplementedError(
                "the paper evaluates image/text routing only; unsupported modalities: "
                + ", ".join(sorted(unsupported))
            )
        factors = self.router.route(analysis)
        image_path = self._image_path(row, media_root) if "image" in analysis.modalities else None
        text = str(row.get("text", ""))
        description = (
            self.backend.generate(IMAGE_DESCRIPTION, image_path)
            if image_path and self.use_image_description
            else ""
        )
        omitted_description = description or "[Image description omitted by ablation]"
        image_value = self.evidence.image(sample_id) if self.use_evidence else None
        text_value = self.evidence.text(sample_id) if self.use_evidence else None
        image_evidence = self.evidence.render_image(image_value, self.retrieval_limit)
        text_evidence = self.evidence.render_text(text_value, self.retrieval_limit)

        if strategy in {"holistic", "joint_factors"}:
            if analysis.modalities != ("image", "text"):
                raise ValueError(f"{strategy} is defined only for image-text inputs")
            template = HOLISTIC_EIGHT_WAY if strategy == "holistic" else JOINT_FACTORS
            raw = self.backend.generate(
                template.format(
                    image_description=omitted_description,
                    text=text,
                    image_evidence=image_evidence,
                    text_evidence=text_evidence,
                ),
                image_path,
            )
            if strategy == "holistic":
                label = parse_label(raw)
                final = decisions_from_label(label)
            else:
                final = parse_structured_decisions(raw, factors)
                label = label_from_decisions(final)
            return StructuredPrediction(
                sample_id,
                analysis.modalities,
                {},
                final,
                label=label,
                image_description=description,
                aggregator_output=raw,
                metadata={
                    "strategy": strategy,
                    "prompt_version": PROMPT_VERSION,
                    "use_evidence": self.use_evidence,
                    "use_image_description": self.use_image_description,
                    "retrieval_limit": self.retrieval_limit,
                },
            )

        outputs: dict[str, FactorResult] = {}
        questions: tuple[str, ...] = ()
        for factor in factors:
            if factor == FactorKey("veracity", "image"):
                raw = self.backend.generate(
                    IMAGE_VERACITY.format(
                        image_description=omitted_description,
                        image_evidence=image_evidence,
                    ),
                    image_path,
                )
            elif factor == FactorKey("veracity", "text"):
                question_raw = self.backend.generate(
                    VERIFICATION_QUESTIONS.format(text=text), None
                )
                questions = parse_questions(question_raw)
                raw = self.backend.generate(
                    TEXT_VERACITY.format(
                        text=text,
                        questions="\n".join(questions),
                        text_evidence=text_evidence,
                    ),
                    None,
                )
            elif factor == FactorKey("consistency", "image", "text"):
                raw = self.backend.generate(
                    IMAGE_TEXT_CONSISTENCY.format(
                        image_description=omitted_description,
                        text=text,
                    ),
                    None,
                )
            else:
                raise NotImplementedError(f"no verifier registered for {factor.id}")
            outputs[factor.id] = parse_factor(raw)

        if strategy == "separate_deterministic":
            aggregator_raw = ""
            final = {key: value.decision for key, value in outputs.items()}
        else:
            payload = {
                factor.display_name: outputs[factor.id].to_dict() for factor in factors
            }
            aggregator_raw = self.backend.generate(
                STRUCTURED_AGGREGATION.format(
                    factor_outputs=json.dumps(payload, ensure_ascii=False, indent=2),
                    modalities=", ".join(analysis.modalities),
                ),
                None,
            )
            final = parse_structured_decisions(aggregator_raw, factors)
        return StructuredPrediction(
            sample_id,
            analysis.modalities,
            outputs,
            final,
            label=label_from_decisions(final),
            image_description=description,
            verification_questions=questions,
            aggregator_output=aggregator_raw,
            metadata={
                "strategy": strategy,
                "prompt_version": PROMPT_VERSION,
                "use_evidence": self.use_evidence,
                "use_image_description": self.use_image_description,
                "retrieval_limit": self.retrieval_limit,
            },
        )
