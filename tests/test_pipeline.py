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


class RecordingBackend(MockBackend):
    def __init__(self):
        self.calls = []

    def generate(self, prompt: str, image_path: str | Path | None = None) -> str:
        self.calls.append((prompt, image_path))
        return super().generate(prompt, image_path)


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

    def test_variant_d_aggregates_each_factor_independently(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        backend = RecordingBackend()
        verifier = SourceAwareVerifier(backend, EvidenceStore(root))
        verifier.predict(
            {
                "sample_id": "synthetic-image-text",
                "image_path": "mock.jpg",
                "text": "synthetic claim",
            },
            strategy="separate_structured",
        )
        factorwise = [
            prompt
            for prompt, _ in backend.calls
            if "Role: Produce the final decision for one verification factor" in prompt
        ]
        cross_factor = [
            prompt
            for prompt, _ in backend.calls
            if "Role: Produce final factor decisions from multiple structured" in prompt
        ]
        self.assertEqual(len(factorwise), 3)
        self.assertEqual(len(cross_factor), 0)
        for prompt in factorwise:
            self.assertNotIn("[ACTIVE FACTOR OUTPUTS]", prompt)

    def test_variant_e_is_the_only_cross_factor_aggregation_path(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        backend = RecordingBackend()
        verifier = SourceAwareVerifier(backend, EvidenceStore(root))
        verifier.predict(
            {
                "sample_id": "synthetic-image-text",
                "image_path": "mock.jpg",
                "text": "synthetic claim",
            },
            strategy="separate_cross_factor",
        )
        factorwise = [
            prompt
            for prompt, _ in backend.calls
            if "Role: Produce the final decision for one verification factor" in prompt
        ]
        cross_factor = [
            prompt
            for prompt, _ in backend.calls
            if "Role: Produce final factor decisions from multiple structured" in prompt
        ]
        self.assertEqual(len(factorwise), 0)
        self.assertEqual(len(cross_factor), 1)
        self.assertIn('"Image Veracity"', cross_factor[0])
        self.assertIn('"Text Veracity"', cross_factor[0])
        self.assertIn('"Image-Text Consistency"', cross_factor[0])

    def test_k0_keeps_evidence_interface_while_no_evidence_removes_it(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        row = {
            "sample_id": "synthetic-image-text",
            "image_path": "mock.jpg",
            "text": "synthetic claim",
        }

        k0_backend = RecordingBackend()
        SourceAwareVerifier(
            k0_backend, EvidenceStore(root), retrieval_limit=0
        ).predict(row, strategy="separate_deterministic")
        k0_prompts = "\n".join(prompt for prompt, _ in k0_backend.calls)
        self.assertIn("[RETRIEVED IMAGE EVIDENCE]", k0_prompts)
        self.assertIn("[RETRIEVED TEXTUAL EVIDENCE]", k0_prompts)
        self.assertIn("retrieval budget k=0", k0_prompts)

        no_evidence_backend = RecordingBackend()
        SourceAwareVerifier(
            no_evidence_backend, EvidenceStore(root), use_evidence=False
        ).predict(row, strategy="separate_deterministic")
        no_evidence_prompts = "\n".join(prompt for prompt, _ in no_evidence_backend.calls)
        self.assertNotIn("[RETRIEVED IMAGE EVIDENCE]", no_evidence_prompts)
        self.assertNotIn("[RETRIEVED TEXTUAL EVIDENCE]", no_evidence_prompts)

    def test_consistency_validator_uses_description_and_text_not_raw_image(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        backend = RecordingBackend()
        SourceAwareVerifier(backend, EvidenceStore(root)).predict(
            {
                "sample_id": "synthetic-image-text",
                "image_path": "mock.jpg",
                "text": "synthetic claim",
            },
            strategy="separate_deterministic",
        )
        consistency_calls = [
            (prompt, image_path)
            for prompt, image_path in backend.calls
            if "Role: Determine whether a salient semantic conflict" in prompt
        ]
        self.assertEqual(len(consistency_calls), 1)
        prompt, image_path = consistency_calls[0]
        self.assertIn("[IMAGE DESCRIPTION]", prompt)
        self.assertIn("[INPUT TEXT]", prompt)
        self.assertIsNone(image_path)

class DualBackendRoutingTests(unittest.TestCase):
    def test_paper_zero_shot_roles_use_multimodal_and_language_backends(self):
        root = Path(__file__).parents[1] / "examples" / "evidence"
        multimodal = RecordingBackend()
        language = RecordingBackend()
        verifier = SourceAwareVerifier(
            multimodal,
            EvidenceStore(root),
            language_backend=language,
        )
        verifier.predict(
            {
                "sample_id": "synthetic-image-text",
                "image_path": "mock.jpg",
                "text": "synthetic claim",
            },
            strategy="separate_structured",
        )

        multimodal_prompts = "\n".join(prompt for prompt, _ in multimodal.calls)
        language_prompts = "\n".join(prompt for prompt, _ in language.calls)

        self.assertIn("Role: Generate a structured description", multimodal_prompts)
        self.assertIn("Role: Verify the factual veracity of the image", multimodal_prompts)
        self.assertNotIn("Role: Generate focused fact-checking questions", multimodal_prompts)
        self.assertNotIn("Role: Verify the factual veracity of the input text", multimodal_prompts)
        self.assertNotIn("Role: Determine whether a salient semantic conflict", multimodal_prompts)
        self.assertNotIn("Role: Produce the final decision for one verification factor", multimodal_prompts)

        self.assertIn("Role: Generate focused fact-checking questions", language_prompts)
        self.assertIn("Role: Verify the factual veracity of the input text", language_prompts)
        self.assertIn("Role: Determine whether a salient semantic conflict", language_prompts)
        self.assertEqual(
            language_prompts.count("Role: Produce the final decision for one verification factor"),
            3,
        )
        self.assertTrue(all(image_path is None for _, image_path in language.calls))
