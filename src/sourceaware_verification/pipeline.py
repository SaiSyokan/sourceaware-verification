"""Paper-aligned source-aware verification pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .backend import Backend
from .evidence import EvidenceStore
from .labels import decisions_from_label, label_from_decisions
from .parsing import (
    parse_factor,
    parse_final_decision,
    parse_label,
    parse_questions,
    parse_structured_decisions,
)
from .prompts import (
    CROSS_FACTOR_AGGREGATION,
    FACTORWISE_STRUCTURED_AGGREGATION,
    HOLISTIC_EIGHT_WAY,
    IMAGE_DESCRIPTION,
    IMAGE_TEXT_CONSISTENCY,
    IMAGE_TEXT_CONSISTENCY_NO_DESCRIPTION,
    IMAGE_VERACITY,
    IMAGE_VERACITY_IMAGE_ONLY,
    IMAGE_VERACITY_NO_DESCRIPTION,
    IMAGE_VERACITY_NO_EVIDENCE,
    JOINT_FACTORS,
    PROMPT_VERSION,
    TEXT_VERACITY,
    TEXT_VERACITY_NO_EVIDENCE,
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
    "separate_cross_factor",
)


class SourceAwareVerifier:
    """Execute active factor modules and aggregate their structured outputs."""

    def __init__(
        self,
        backend: Backend,
        evidence: EvidenceStore,
        *,
        language_backend: Backend | None = None,
        use_evidence: bool = True,
        use_image_description: bool = True,
        retrieval_limit: int = 3,
    ) -> None:
        if retrieval_limit < 0:
            raise ValueError("retrieval_limit must be non-negative")
        # ``backend`` is the multimodal backend kept as the first positional
        # argument for backwards compatibility. Paper-faithful zero-shot runs
        # should additionally provide ``language_backend`` for text-only calls.
        self.backend = backend
        self.multimodal_backend = backend
        self.language_backend = language_backend or backend
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

    def _image_veracity_prompt(self, description: str, image_evidence: str) -> str:
        if self.use_evidence and self.use_image_description:
            return IMAGE_VERACITY.format(
                image_description=description,
                image_evidence=image_evidence,
            )
        if self.use_evidence:
            return IMAGE_VERACITY_NO_DESCRIPTION.format(image_evidence=image_evidence)
        if self.use_image_description:
            return IMAGE_VERACITY_NO_EVIDENCE.format(image_description=description)
        return IMAGE_VERACITY_IMAGE_ONLY

    def _text_veracity_prompt(
        self, text: str, questions: tuple[str, ...], text_evidence: str
    ) -> str:
        if self.use_evidence:
            return TEXT_VERACITY.format(
                text=text,
                questions="\n".join(questions),
                text_evidence=text_evidence,
            )
        return TEXT_VERACITY_NO_EVIDENCE.format(
            text=text,
            questions="\n".join(questions),
        )

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
            self.multimodal_backend.generate(IMAGE_DESCRIPTION, image_path)
            if image_path and self.use_image_description
            else ""
        )
        image_value = self.evidence.image(sample_id) if self.use_evidence else None
        text_value = self.evidence.text(sample_id) if self.use_evidence else None
        image_evidence = self.evidence.render_image(image_value, self.retrieval_limit)
        text_evidence = self.evidence.render_text(text_value, self.retrieval_limit)

        if strategy in {"holistic", "joint_factors"}:
            if analysis.modalities != ("image", "text"):
                raise ValueError(f"{strategy} is defined only for image-text inputs")
            template = HOLISTIC_EIGHT_WAY if strategy == "holistic" else JOINT_FACTORS
            raw = self.multimodal_backend.generate(
                template.format(
                    image_description=description or "[Image description omitted by ablation]",
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
                raw = self.multimodal_backend.generate(
                    self._image_veracity_prompt(description, image_evidence),
                    image_path,
                )
            elif factor == FactorKey("veracity", "text"):
                question_raw = self.language_backend.generate(
                    VERIFICATION_QUESTIONS.format(text=text), None
                )
                questions = parse_questions(question_raw)
                raw = self.language_backend.generate(
                    self._text_veracity_prompt(text, questions, text_evidence),
                    None,
                )
            elif factor == FactorKey("consistency", "image", "text"):
                if self.use_image_description:
                    prompt = IMAGE_TEXT_CONSISTENCY.format(
                        image_description=description,
                        text=text,
                    )
                else:
                    prompt = IMAGE_TEXT_CONSISTENCY_NO_DESCRIPTION.format(text=text)
                # The consistency validator consumes the structured image
                # description and input text. The raw image is used only by
                # the description step, matching the image-text instantiation
                # in the frozen manuscript.
                raw = self.language_backend.generate(prompt, None)
            else:
                raise NotImplementedError(f"no verifier registered for {factor.id}")
            outputs[factor.id] = parse_factor(raw)

        if strategy == "separate_deterministic":
            aggregator_raw = ""
            final = {key: value.decision for key, value in outputs.items()}
        elif strategy == "separate_structured":
            final: dict[str, str] = {}
            aggregation_outputs: dict[str, str] = {}
            for factor in factors:
                result = outputs[factor.id]
                raw = self.language_backend.generate(
                    FACTORWISE_STRUCTURED_AGGREGATION.format(
                        decision=result.decision,
                        confidence=result.confidence,
                        explanation=result.explanation,
                    ),
                    None,
                )
                aggregation_outputs[factor.id] = raw
                final[factor.id] = parse_final_decision(raw)
            aggregator_raw = json.dumps(aggregation_outputs, ensure_ascii=False, sort_keys=True)
        else:  # Variant E: cross-factor aggregation.
            payload = {
                factor.display_name: outputs[factor.id].to_dict() for factor in factors
            }
            aggregator_raw = self.language_backend.generate(
                CROSS_FACTOR_AGGREGATION.format(
                    factor_outputs=json.dumps(payload, ensure_ascii=False, indent=2),
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
