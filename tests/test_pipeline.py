from pathlib import Path

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
        if "Role: Determine whether the image and text" in prompt:
            return "Decision: F\nConfidence: 0.9\nExplanation: the modalities describe different situations"
        if "Role: Produce the final structured prediction" in prompt:
            lines = []
            if '"Image Veracity"' in prompt:
                lines.append("Image Veracity: F")
            if '"Text Veracity"' in prompt:
                lines.append("Text Veracity: T")
            if '"Image-Text Consistency"' in prompt:
                lines.append("Image-Text Consistency: F")
            lines.append("Explanation: joint review retained the factor outputs")
            return "\n".join(lines)
        if "Predict one image-text label" in prompt:
            return "Label: FTF"
        if "Jointly predict image veracity" in prompt:
            return "Image Veracity: F\nText Veracity: T\nImage-Text Consistency: F"
        raise AssertionError(f"unexpected prompt: {prompt[:80]}")


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
        self.assertEqual(self.verifier.predict(row, strategy="holistic").label, "FTF")
        self.assertEqual(self.verifier.predict(row, strategy="joint_factors").label, "FTF")
        self.assertEqual(
            self.verifier.predict(row, strategy="separate_deterministic").label, "FTF"
        )

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
