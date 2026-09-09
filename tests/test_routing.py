import unittest

from sourceaware_verification.routing import InputAnalyzer, VerificationRouter


class RoutingTests(unittest.TestCase):
    def test_image_text_routing_matches_factor_space(self):
        analysis = InputAnalyzer().analyze({"image_path": "image.jpg", "text": "claim"})
        self.assertEqual(analysis.modalities, ("image", "text"))
        self.assertEqual(analysis.relations, (("image", "text"),))
        self.assertEqual(
            [factor.id for factor in VerificationRouter().route(analysis)],
            ["veracity:image", "veracity:text", "consistency:image:text"],
        )

    def test_single_modality_activates_only_its_veracity(self):
        analysis = InputAnalyzer().analyze({"text": "claim"})
        self.assertEqual(
            [factor.id for factor in VerificationRouter().route(analysis)], ["veracity:text"]
        )

    def test_general_analyzer_orders_modalities_and_relations(self):
        analysis = InputAnalyzer().analyze({"modalities": ["video", "audio", "text"]})
        self.assertEqual(analysis.modalities, ("text", "audio", "video"))
        self.assertEqual(
            analysis.relations,
            (("text", "audio"), ("text", "video"), ("audio", "video")),
        )
