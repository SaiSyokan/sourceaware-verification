from pathlib import Path

import json
import unittest

from sourceaware_verification.evidence import EvidenceStore
from sourceaware_verification.pipeline import SourceAwareVerifier


class MockBackend:
    def generate(self, prompt: str, image_path: str | Path | None = None) -> str:
        if "Role: Generate a structured description" in prompt:
            return "A structured synthetic image description."
        if "Role: Generate focused fact-checking questions" in prompt:
            return "1. Did the stated event occur?\n2. Is the named entity correct?"
        if "Role: Verify the factual veracity of the image" in prompt:
            return "Decision: F\nConfidence: 0.8\nExplanation: image evidence contradicts a material attribute"
        if "Role: Verify the factual veracity of the input text" in prompt:
            return "Decision: T\nConfidence: 0.7\nExplanation: no textual violation was identified"
        if "Role: Determine whether a salient semantic conflict" in prompt:
            return "Decision: F\nConfidence: 0.9\nExplanation: the modalities describe different situations"
        if "Role: Produce the final decision for one verification factor" in prompt:
            if "[FACTOR DECISION]\nF" in prompt:
                return "Final Decision: F"
            return "Final Decision: T"
        if "Role: Produce final factor decisions from multiple structured" in prompt:
            lines = []
            if '"Image Veracity"' in prompt:
                lines.append("Image Veracity: F")
            if '"Text Veracity"' in prompt:
                lines.append("Text Veracity: T")
            if '"Image-Text Consistency"' in prompt:
                lines.append("Image-Text Consistency: F")
            return "\n".join(lines)
        if "Predict one image-text label" in prompt:
            return "Label: FTF"
        if "Jointly predict image veracity" in prompt:
            return "Image Veracity: F\nText Veracity: T\nImage-Text Consistency: F"
        raise AssertionError(f"unexpected prompt: {prompt[:100]}")


class PipelineTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        self.verifier = SourceAwareVerifier(MockBackend(), EvidenceStore(root))

    def test_primary_image_text_path(self):
        result = self.verifier.predict(
            {
                "sample_id": "synthetic-image-text",
                "image_path": "missing-is-okay-for-mock.jpg",
                "text": "synthetic claim",
            }
        )
        self.assertEqual(result.label, "FTF")
        self.assertEqual(
            result.final_decisions,
            {
                "veracity:image": "F",
                "veracity:text": "T",
                "consistency:image:text": "F",
            },
        )
        self.assertEqual(len(result.verification_questions), 2)
        self.assertEqual(len(result.module_outputs), 3)
        per_factor = json.loads(result.aggregator_output)
        self.assertEqual(set(per_factor), set(result.final_decisions))

    def test_text_only_dynamic_routing(self):
        result = self.verifier.predict({"sample_id": "text-only", "text": "synthetic claim"})
        self.assertEqual(result.modalities, ("text",))
        self.assertEqual(result.final_decisions, {"veracity:text": "T"})
        self.assertIsNone(result.label)

    def test_framework_ablation_paths(self):
        row = {
            "sample_id": "synthetic-image-text",
            "image_path": "mock.jpg",
            "text": "synthetic claim",
        }
        for strategy in (
            "holistic",
            "joint_factors",
            "separate_deterministic",
            "separate_structured",
            "separate_cross_factor",
        ):
            self.assertEqual(self.verifier.predict(row, strategy=strategy).label, "FTF")

    def test_unsupported_modality_is_explicit(self):
        with self.assertRaisesRegex(NotImplementedError, "audio"):
            self.verifier.predict({"sample_id": "audio", "audio_path": "audio.wav"})

    def test_module_ablation_can_omit_image_description(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        verifier = SourceAwareVerifier(
            MockBackend(), EvidenceStore(root), use_image_description=False
        )
        result = verifier.predict(
            {"sample_id": "synthetic-image-text", "image_path": "mock.jpg", "text": "claim"}
        )
        self.assertEqual(result.image_description, "")
        self.assertFalse(result.metadata["use_image_description"])

    def test_k_zero_is_distinct_from_without_evidence(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        k0 = SourceAwareVerifier(MockBackend(), EvidenceStore(root), retrieval_limit=0)
        no_evidence = SourceAwareVerifier(
            MockBackend(), EvidenceStore(root), use_evidence=False, retrieval_limit=3
        )
        self.assertEqual(k0.retrieval_limit, 0)
        self.assertTrue(k0.use_evidence)
        self.assertFalse(no_evidence.use_evidence)
